"""
server.py

FastAPI server for NUGovern HTTP API.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, UTC

from .models import (
    OperationRequest, OperationResponse,
    PolicyRequest, PolicyResponse,
    LedgerQuery, LedgerEntryResponse,
    MonitorStatsResponse, HealthResponse,
    AttestationRequest, AttestationResponse
)

from src.nucore import add, multiply, compose, catch, flip
from src.nucore.validators import coverage_ratio, validate
from src.nuledger import Ledger, MemoryBackend
from src.nuguard import Monitor, MonitorConfig
from src.nupolicy import PolicyManager, Policy, PolicyConfig
from src.nupolicy.integration import create_monitor_from_policy


class NUGovernServer:
    """
    NUGovern server instance with stateful components

    Maintains:
    - Ledger for operation logging
    - Monitor for runtime checking
    - PolicyManager for policy lifecycle
    """

    def __init__(
        self,
        ledger_backend=None,
        policy_dir: Optional[Path] = None
    ):
        """
        Initialize NUGovern server

        Args:
            ledger_backend: Ledger backend (defaults to MemoryBackend)
            policy_dir: Directory for policy files
        """
        self.ledger = Ledger(backend=ledger_backend or MemoryBackend())
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

            # Execute operation
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

            # Validate result
            invariant_passed = validate(n_out, u_out)

            # Calculate coverage
            cov = coverage_ratio(n_out, u_out)

            # Monitor operation
            event = self.monitor.check(
                request.operation.value,
                inputs,
                (n_out, u_out)
            )

            # Log to ledger if auto_log enabled
            ledger_id = None
            if self.monitor.config.auto_log:
                entry = self.ledger.append(
                    operation=request.operation.value,
                    inputs=inputs,
                    output=(n_out, u_out),
                    coverage=cov,
                    invariant_passed=invariant_passed
                )
                ledger_id = entry.op_id

            return OperationResponse(
                result=(n_out, u_out),
                coverage=cov,
                invariant_passed=invariant_passed,
                ledger_id=ledger_id
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    def load_policy(self, name: str) -> PolicyResponse:
        """
        Load policy and reconfigure monitor

        Args:
            name: Policy name

        Returns:
            Policy response

        Raises:
            HTTPException: If policy not found
        """
        try:
            policy = self.policy_manager.load_policy(name)
            self.current_policy = policy

            # Reconfigure monitor
            self.monitor = create_monitor_from_policy(
                policy,
                ledger=self.ledger,
                validate=False
            )

            return PolicyResponse(
                name=policy.config.name,
                version=policy.config.version,
                description=policy.config.description,
                policy_hash=policy.policy_hash,
                signed=policy.signature is not None,
                rules_count=len(policy.config.rules)
            )

        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy '{name}' not found"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    def create_policy(self, request: PolicyRequest) -> PolicyResponse:
        """
        Create new policy

        Args:
            request: Policy creation request

        Returns:
            Policy response

        Raises:
            HTTPException: If policy creation fails
        """
        try:
            policy = self.policy_manager.create_policy(
                name=request.name,
                description=request.description,
                rules=request.rules,
                escalation=request.escalation,
                metadata=request.metadata
            )

            # Override version if provided
            if request.version:
                policy.config.version = request.version

            # Recompute hash after version change
            policy.policy_hash = policy._compute_hash()

            # Save policy
            self.policy_manager.save_policy(policy, request.name)

            return PolicyResponse(
                name=policy.config.name,
                version=policy.config.version,
                description=policy.config.description,
                policy_hash=policy.policy_hash,
                signed=False,
                rules_count=len(policy.config.rules)
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    def get_ledger_entries(self, query: LedgerQuery) -> List[LedgerEntryResponse]:
        """
        Query ledger entries

        Args:
            query: Query parameters

        Returns:
            List of ledger entries
        """
        try:
            if query.operation_id:
                # Trace specific operation
                chain = self.ledger.trace(query.operation_id)
                entries = chain
            else:
                # Get all entries with pagination
                all_entries = self.ledger.get_all()
                start = query.offset
                end = query.offset + query.limit
                entries = all_entries[start:end]

            return [
                LedgerEntryResponse(
                    op_id=entry.op_id,
                    timestamp=entry.timestamp,
                    operation=entry.operation,
                    inputs=entry.inputs,
                    output=entry.output,
                    coverage=entry.coverage,
                    invariant_passed=entry.invariant_passed,
                    parent_id=entry.parent_id,
                    signature=entry.signature
                )
                for entry in entries
            ]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


def create_app(server: Optional[NUGovernServer] = None) -> FastAPI:
    """
    Create FastAPI application

    Args:
        server: Optional NUGovernServer instance (creates default if None)

    Returns:
        FastAPI app
    """
    if server is None:
        server = NUGovernServer()

    app = FastAPI(
        title="NUGovern API",
        description="HTTP API for eBIOS Governance and Policy Management",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    @app.get("/", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint"""
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            layers={
                "nucore": True,
                "nuledger": True,
                "nuguard": True,
                "nupolicy": True
            }
        )

    @app.post("/operations/execute", response_model=OperationResponse)
    async def execute_operation(request: OperationRequest):
        """Execute NUCore operation with monitoring"""
        return server.execute_operation(request)

    @app.get("/policies", response_model=List[str])
    async def list_policies():
        """List all available policies"""
        return server.policy_manager.list_policies()

    @app.post("/policies", response_model=PolicyResponse)
    async def create_policy(request: PolicyRequest):
        """Create new policy"""
        return server.create_policy(request)

    @app.get("/policies/{name}", response_model=PolicyResponse)
    async def get_policy(name: str):
        """Load policy by name"""
        return server.load_policy(name)

    @app.put("/policies/{name}/activate")
    async def activate_policy(name: str):
        """Activate policy (reconfigure monitor)"""
        response = server.load_policy(name)
        return {"message": f"Policy '{name}' activated", "policy": response}

    @app.get("/ledger/entries", response_model=List[LedgerEntryResponse])
    async def get_ledger_entries(
        operation_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """Query ledger entries"""
        query = LedgerQuery(operation_id=operation_id, limit=limit, offset=offset)
        return server.get_ledger_entries(query)

    @app.get("/ledger/verify")
    async def verify_ledger():
        """Verify ledger integrity"""
        is_valid = server.ledger.verify_integrity()
        return {
            "valid": is_valid,
            "entries": len(server.ledger),
            "root": server.ledger.get_root()
        }

    @app.get("/monitor/stats", response_model=MonitorStatsResponse)
    async def get_monitor_stats():
        """Get monitor statistics"""
        stats = server.monitor.stats()
        return MonitorStatsResponse(**stats)

    @app.post("/monitor/reset")
    async def reset_monitor():
        """Reset monitor statistics"""
        server.monitor.reset()
        return {"message": "Monitor statistics reset"}

    @app.post("/attestation", response_model=AttestationResponse)
    async def create_attestation(request: AttestationRequest):
        """Create cryptographic attestation"""
        # Simple attestation using policy hash or ledger root
        if request.attestation_type == "policy" and request.target_id:
            try:
                policy = server.policy_manager.load_policy(request.target_id)
                return AttestationResponse(
                    attestation_type="policy",
                    target_id=request.target_id,
                    timestamp=datetime.now(UTC).isoformat(),
                    hash=policy.policy_hash,
                    signature=policy.signature or "unsigned",
                    verified=policy.signature is not None
                )
            except:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Policy '{request.target_id}' not found"
                )

        elif request.attestation_type == "ledger":
            return AttestationResponse(
                attestation_type="ledger",
                target_id="root",
                timestamp=datetime.now(UTC).isoformat(),
                hash=server.ledger.get_root(),
                signature="merkle_root",
                verified=server.ledger.verify_integrity()
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid attestation type or missing target_id"
            )

    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
