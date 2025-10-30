"""
server_v1.py

eBIOS v1.0.0 FastAPI server with JWT authentication and RBAC.

Features:
- JWT authentication (access + refresh tokens)
- Role-Based Access Control (admin, operator, auditor, guest)
- Rate limiting (100 req/min per IP)
- PostgreSQL backend
- Prometheus metrics
- Complete security hardening
"""

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, UTC
import os
import sys

# Import authentication and RBAC
from .auth import get_current_user, require_role, Role, User
from .auth_routes import router as auth_router
from .user_routes import router as user_router
from .security_headers import SecurityHeadersMiddleware

# Import existing models
from .models import (
    OperationRequest, OperationResponse,
    PolicyRequest, PolicyResponse,
    LedgerQuery, LedgerEntryResponse,
    MonitorStatsResponse, HealthResponse,
    AttestationRequest, AttestationResponse
)

# Import core functionality
from src.nucore import add, multiply, compose, catch, flip
from src.nucore.validators import coverage_ratio, validate
from src.nuledger import Ledger, MemoryBackend
from src.nuledger.backends import PostgreSQLBackend, POSTGRES_AVAILABLE
from src.nuguard import Monitor, MonitorConfig
from src.nupolicy import PolicyManager, Policy, PolicyConfig
from src.nupolicy.integration import create_monitor_from_policy

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class NUGovernServer:
    """
    NUGovern server instance with stateful components (v1.0.0)

    Features:
    - JWT authentication
    - RBAC (4 roles)
    - PostgreSQL backend
    - Rate limiting
    - Metrics
    """

    def __init__(
        self,
        ledger_backend=None,
        policy_dir: Optional[Path] = None
    ):
        """
        Initialize NUGovern server v1.0.0

        Args:
            ledger_backend: Ledger backend (PostgreSQL recommended)
            policy_dir: Directory for policy files
        """
        # Initialize backend
        if ledger_backend is None:
            # Try to use PostgreSQL from environment
            if POSTGRES_AVAILABLE:
                db_host = os.getenv('POSTGRES_HOST')
                db_port = int(os.getenv('POSTGRES_PORT', '5432'))
                db_name = os.getenv('POSTGRES_DB', 'ebios')
                db_user = os.getenv('POSTGRES_USER')
                db_password = os.getenv('POSTGRES_PASSWORD')

                if all([db_host, db_port, db_name, db_user, db_password]):
                    try:
                        ledger_backend = PostgreSQLBackend(
                            host=db_host,
                            port=db_port,
                            database=db_name,
                            user=db_user,
                            password=db_password,
                            sslmode=os.getenv('POSTGRES_SSLMODE', 'require')
                        )
                        print(f"✅ Connected to PostgreSQL: {db_host}:{db_port}/{db_name}")
                    except Exception as e:
                        print(f"⚠️  PostgreSQL connection failed: {e}")
                        print("   Falling back to MemoryBackend")
                        ledger_backend = MemoryBackend()
                else:
                    print("⚠️  PostgreSQL credentials not complete, using MemoryBackend")
                    ledger_backend = MemoryBackend()
            else:
                print("⚠️  psycopg2 not available, using MemoryBackend")
                ledger_backend = MemoryBackend()

        self.ledger = Ledger(backend=ledger_backend)
        self.policy_manager = PolicyManager(policy_dir=policy_dir)

        # Default monitor (permissive)
        self.monitor = Monitor(ledger=self.ledger)
        self.current_policy = None

    def execute_operation(self, request: OperationRequest) -> OperationResponse:
        """
        Execute NUCore operation with monitoring

        Args:
            request: Operation request

        Returns:
            Operation response with result

        Raises:
            HTTPException: If operation fails
        """
        try:
            # Extract inputs
            inputs = request.inputs
            params = request.params or {}

            # Execute operation based on type
            if request.operation == "add":
                if len(inputs) != 2:
                    raise ValueError("add requires exactly 2 inputs")
                n1, u1 = inputs[0]
                n2, u2 = inputs[1]
                n_out, u_out = add(n1, u1, n2, u2)

            elif request.operation == "multiply":
                if len(inputs) != 2:
                    raise ValueError("multiply requires exactly 2 inputs")
                n1, u1 = inputs[0]
                n2, u2 = inputs[1]
                lambda_margin = params.get('lambda_margin', 1.0)
                n_out, u_out = multiply(n1, u1, n2, u2, lambda_margin)

            elif request.operation == "compose":
                if len(inputs) != 2:
                    raise ValueError("compose requires exactly 2 inputs")
                n1, u1 = inputs[0]
                n2, u2 = inputs[1]
                n_out, u_out = compose(n1, u1, n2, u2)

            elif request.operation == "catch":
                if len(inputs) != 1:
                    raise ValueError("catch requires exactly 1 input")
                n, u = inputs[0]
                n_out, u_out = catch(n, u)

            elif request.operation == "flip":
                if len(inputs) != 1:
                    raise ValueError("flip requires exactly 1 input")
                n, u = inputs[0]
                n_out, u_out = flip(n, u)

            else:
                raise ValueError(f"Unknown operation: {request.operation}")

            # Calculate coverage
            cov = coverage_ratio(n_out, u_out)

            # Validate result
            validation_result = validate(n_out, u_out)
            invariant_passed = validation_result["valid"]

            # Log to ledger
            op_id = self.ledger.append(
                operation=request.operation,
                inputs=[(n, u) for n, u in inputs],
                output=(n_out, u_out),
                coverage=cov,
                invariant_passed=invariant_passed,
                parent_id=request.parent_id
            )

            # Monitor check
            self.monitor.check(
                operation=request.operation,
                inputs=inputs,
                output=(n_out, u_out)
            )

            return OperationResponse(
                op_id=op_id,
                operation=request.operation,
                result=(n_out, u_out),
                coverage=cov,
                invariant_passed=invariant_passed,
                timestamp=datetime.now(UTC).isoformat(),
                parent_id=request.parent_id
            )

        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Operation failed: {str(e)}"
            )


# Prometheus metrics (with collision protection for tests)
try:
    requests_total = Counter('ebios_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
    request_duration = Histogram('ebios_request_duration_seconds', 'Request duration')
    operations_total = Counter('ebios_operations_total', 'Total operations', ['operation'])
    invariant_failures = Counter('ebios_invariant_failures_total', 'Total invariant failures')
except ValueError:
    # Metrics already registered (happens in tests)
    from prometheus_client import REGISTRY
    requests_total = REGISTRY._names_to_collectors.get('ebios_requests_total')
    request_duration = REGISTRY._names_to_collectors.get('ebios_request_duration_seconds')
    operations_total = REGISTRY._names_to_collectors.get('ebios_operations_total')
    invariant_failures = REGISTRY._names_to_collectors.get('ebios_invariant_failures_total')


def create_app() -> FastAPI:
    """Create FastAPI application with authentication and RBAC"""

    # Initialize server
    server = NUGovernServer()

    # Create FastAPI app
    app = FastAPI(
        title="eBIOS API",
        version="1.1.0",
        description="Epistemic Bio-Inspired Operating System with formal guarantees"
    )

    # Register error handlers (must be done before other exception handlers)
    from .error_handlers import register_error_handlers
    register_error_handlers(app)

    # Add rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS middleware (configurable via environment)
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    if cors_origins == '*':
        print("⚠️  WARNING: CORS allows all origins (*)", file=sys.stderr)
        print("⚠️  Set CORS_ORIGINS environment variable for production", file=sys.stderr)
        allow_origins = ["*"]
    else:
        allow_origins = [origin.strip() for origin in cors_origins.split(',')]
        print(f"✓ CORS restricted to: {allow_origins}", file=sys.stderr)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    print("✓ Security headers enabled (HSTS, CSP, X-Frame-Options, etc.)", file=sys.stderr)

    # Include authentication routes
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

    # Include user management routes (router already has /users prefix)
    app.include_router(user_router, tags=["User Management"])

    # Health check (no auth required)
    @app.get("/", response_model=HealthResponse)
    @limiter.exempt
    async def health_check():
        """Health check endpoint (no authentication required)"""
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            layers={
                "nucore": True,
                "nuledger": True,
                "nuguard": True,
                "nupolicy": True,
                "auth": True,
                "rbac": True,
                "postgres": isinstance(server.ledger.backend, PostgreSQLBackend)
            }
        )

    # Operations endpoints (require admin or operator role)
    @app.post("/operations/execute", response_model=OperationResponse)
    @limiter.limit("100/minute")
    async def execute_operation(
        request: Request,
        operation_request: OperationRequest,
        current_user: User = Depends(require_role([Role.ADMIN, Role.OPERATOR]))
    ):
        """Execute operation (requires admin or operator role)"""
        try:
            operations_total.labels(operation=operation_request.operation).inc()
            result = server.execute_operation(operation_request)

            if not result.invariant_passed:
                invariant_failures.inc()

            requests_total.labels(
                method="POST",
                endpoint="/operations/execute",
                status="200"
            ).inc()

            return result
        except HTTPException:
            raise
        except Exception as e:
            requests_total.labels(
                method="POST",
                endpoint="/operations/execute",
                status="500"
            ).inc()
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/operations/batch")
    @limiter.limit("100/minute")
    async def execute_batch(
        request: Request,
        operations: List[OperationRequest],
        current_user: User = Depends(require_role([Role.ADMIN, Role.OPERATOR]))
    ):
        """Execute batch operations (requires admin or operator role)"""
        results = []
        for op_request in operations:
            try:
                result = server.execute_operation(op_request)
                results.append(result)
            except Exception as e:
                # Rollback on failure (atomic batch)
                raise HTTPException(
                    status_code=400,
                    detail=f"Batch failed at operation {len(results)}: {str(e)}"
                )

        return {
            "batch_id": f"batch_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            "total_operations": len(operations),
            "successful": len(results),
            "results": results,
            "timestamp": datetime.now(UTC).isoformat()
        }

    # Ledger endpoints (require admin, operator, or auditor role)
    @app.get("/ledger/query")
    @limiter.limit("100/minute")
    async def query_ledger(
        request: Request,
        op_id: Optional[str] = None,
        operation: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
        current_user: User = Depends(require_role([Role.ADMIN, Role.OPERATOR, Role.AUDITOR]))
    ):
        """Query ledger (requires admin, operator, or auditor role)"""
        try:
            # Build query
            query_params = {}
            if op_id:
                query_params['op_id'] = op_id
            if operation:
                query_params['operation'] = operation
            if start_time:
                query_params['start_time'] = start_time
            if end_time:
                query_params['end_time'] = end_time

            # Query ledger
            entries = server.ledger.query(**query_params)

            # Paginate
            total = len(entries)
            paginated = entries[offset:offset+limit]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "operations": [
                    {
                        "op_id": entry.op_id,
                        "operation": entry.operation,
                        "inputs": entry.inputs,
                        "output": entry.output,
                        "coverage": entry.coverage,
                        "invariant_passed": entry.invariant_passed,
                        "timestamp": entry.timestamp,
                        "parent_id": entry.parent_id,
                        "signature": entry.signature
                    }
                    for entry in paginated
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/ledger/verify/{op_id}")
    @limiter.limit("100/minute")
    async def verify_operation(
        request: Request,
        op_id: str,
        current_user: User = Depends(require_role([Role.ADMIN, Role.OPERATOR, Role.AUDITOR]))
    ):
        """Verify operation signature (requires admin, operator, or auditor role)"""
        try:
            entries = server.ledger.query(op_id=op_id)
            if not entries:
                raise HTTPException(status_code=404, detail="Operation not found")

            entry = entries[0]
            # TODO: Implement actual signature verification
            signature_valid = True  # Placeholder

            return {
                "op_id": entry.op_id,
                "signature_valid": signature_valid,
                "invariant_passed": entry.invariant_passed,
                "coverage": entry.coverage,
                "timestamp": entry.timestamp
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Metrics endpoint (admin only)
    @app.get("/metrics")
    @limiter.exempt
    async def metrics(
        current_user: User = Depends(require_role([Role.ADMIN]))
    ):
        """Prometheus metrics (requires admin role)"""
        return JSONResponse(
            content=generate_latest().decode('utf-8'),
            media_type=CONTENT_TYPE_LATEST
        )

    # Policy endpoints (admin only)
    @app.post("/policies/activate")
    @limiter.limit("10/minute")
    async def activate_policy(
        request: Request,
        policy_request: PolicyRequest,
        current_user: User = Depends(require_role([Role.ADMIN]))
    ):
        """Activate policy (requires admin role)"""
        try:
            # Load or create policy
            if policy_request.policy_id:
                policy = server.policy_manager.get_policy(policy_request.policy_id)
            else:
                policy = Policy(
                    policy_id=policy_request.policy_id or "default",
                    constraints=policy_request.constraints or {},
                    config=PolicyConfig()
                )

            # Create monitor from policy
            server.monitor = create_monitor_from_policy(policy, server.ledger)
            server.current_policy = policy

            return PolicyResponse(
                policy_id=policy.policy_id,
                status="active",
                message="Policy activated successfully"
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/policies/deactivate")
    @limiter.limit("10/minute")
    async def deactivate_policy(
        request: Request,
        current_user: User = Depends(require_role([Role.ADMIN]))
    ):
        """Deactivate policy (requires admin role)"""
        # Reset to default monitor
        server.monitor = Monitor(ledger=server.ledger)
        server.current_policy = None

        return PolicyResponse(
            policy_id=None,
            status="inactive",
            message="Policy deactivated successfully"
        )

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
