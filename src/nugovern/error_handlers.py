"""
error_handlers.py

Structured error handling for eBIOS API v1.1.0

Provides:
- Consistent error response format
- Detailed error information for debugging
- Production-safe error messages (no sensitive data leaks)
- Request ID tracking for debugging
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional, Dict, Any, List
from datetime import datetime, UTC
import traceback
import uuid


class ErrorResponse:
    """Structured error response"""

    def __init__(
        self,
        error: str,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        path: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.request_id = request_id or str(uuid.uuid4())
        self.path = path
        self.timestamp = timestamp or datetime.now(UTC).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        response = {
            "error": self.error,
            "message": self.message,
            "status_code": self.status_code,
            "request_id": self.request_id,
            "timestamp": self.timestamp
        }

        if self.path:
            response["path"] = self.path

        if self.details:
            response["details"] = self.details

        return response


# Error code mapping
ERROR_CODES = {
    # Client errors (4xx)
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",

    # Server errors (5xx)
    500: "INTERNAL_SERVER_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT"
}


def get_error_code(status_code: int) -> str:
    """Get error code from status code"""
    return ERROR_CODES.get(status_code, f"HTTP_{status_code}")


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTPException with structured error response

    Args:
        request: FastAPI request
        exc: HTTPException

    Returns:
        Structured JSON error response
    """
    error_code = get_error_code(exc.status_code)

    error_response = ErrorResponse(
        error=error_code,
        message=exc.detail,
        status_code=exc.status_code,
        path=request.url.path
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors with detailed field information

    Args:
        request: FastAPI request
        exc: RequestValidationError

    Returns:
        Structured JSON error response with validation details
    """
    # Extract validation errors
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    error_response = ErrorResponse(
        error="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": validation_errors},
        path=request.url.path
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.to_dict()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        Structured JSON error response (without sensitive details in production)
    """
    # Get exception details
    exc_type = type(exc).__name__
    exc_message = str(exc)

    # In development, include traceback
    import os
    debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'

    details = {
        "exception_type": exc_type
    }

    if debug_mode:
        details["exception_message"] = exc_message
        details["traceback"] = traceback.format_exc()

    error_response = ErrorResponse(
        error="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
        path=request.url.path
    )

    # Log the error (in production, use proper logging)
    print(f"ERROR [{error_response.request_id}]: {exc_type}: {exc_message}")
    if debug_mode:
        print(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.to_dict()
    )


# Custom exception classes
class EBIOSException(Exception):
    """Base exception for eBIOS API"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or get_error_code(status_code)
        self.details = details or {}
        super().__init__(self.message)


class InvariantViolationError(EBIOSException):
    """Raised when operation violates mathematical invariants"""

    def __init__(
        self,
        message: str = "Operation violates mathematical invariants",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVARIANT_VIOLATION",
            details=details
        )


class PolicyViolationError(EBIOSException):
    """Raised when operation violates active policy"""

    def __init__(
        self,
        message: str = "Operation violates active policy",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="POLICY_VIOLATION",
            details=details
        )


class DatabaseError(EBIOSException):
    """Raised when database operation fails"""

    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details
        )


class AuthenticationError(EBIOSException):
    """Raised when authentication fails"""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class AuthorizationError(EBIOSException):
    """Raised when authorization fails"""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )


async def ebios_exception_handler(request: Request, exc: EBIOSException) -> JSONResponse:
    """
    Handle custom eBIOS exceptions

    Args:
        request: FastAPI request
        exc: EBIOSException

    Returns:
        Structured JSON error response
    """
    error_response = ErrorResponse(
        error=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict()
    )


def register_error_handlers(app):
    """
    Register all error handlers with FastAPI app

    Args:
        app: FastAPI application instance
    """
    from fastapi import FastAPI
    from starlette.exceptions import HTTPException as StarletteHTTPException

    # Register custom exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(EBIOSException, ebios_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    print("✓ Error handlers registered (structured responses enabled)", file=__import__('sys').stderr)
