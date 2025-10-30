"""
auth.py

JWT Authentication and Authorization for NUGovern API

Provides:
- User authentication with JWT tokens
- Role-Based Access Control (RBAC)
- Password hashing and verification
- Token generation and validation
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import secrets
import os
import sys

# Security configuration
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    print("⚠️  WARNING: SECRET_KEY not set in environment!", file=sys.stderr)
    print("⚠️  Using randomly generated key - tokens will be invalidated on restart!", file=sys.stderr)
    print("⚠️  Set SECRET_KEY environment variable for production use.", file=sys.stderr)
    SECRET_KEY = secrets.token_urlsafe(32)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '30'))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


# Roles
class Role:
    """User roles for RBAC"""
    ADMIN = "admin"      # Full access
    OPERATOR = "operator"  # Execute operations, query ledger
    AUDITOR = "auditor"   # Read-only access
    GUEST = "guest"       # Health check only

    ALL_ROLES = [ADMIN, OPERATOR, AUDITOR, GUEST]


# Models
class User(BaseModel):
    """User model"""
    username: str
    role: str
    disabled: bool = False


class UserInDB(User):
    """User model with hashed password"""
    hashed_password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class TokenData(BaseModel):
    """Data embedded in JWT token"""
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Login credentials"""
    username: str
    password: str


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


# User utilities
def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database"""
    from .user_db import get_user_db
    db = get_user_db()
    return db.get_user(username)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# Token utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(username=username, role=role)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user from token"""
    token = credentials.credentials
    token_data = decode_token(token)

    user = get_user(username=token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )

    return User(username=user.username, role=user.role, disabled=user.disabled)


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# RBAC utilities
def require_role(allowed_roles: List[str]):
    """Decorator to require specific roles"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker


# Convenience dependencies for common role checks
require_admin = Depends(require_role([Role.ADMIN]))
require_operator = Depends(require_role([Role.ADMIN, Role.OPERATOR]))
require_auditor = Depends(require_role([Role.ADMIN, Role.OPERATOR, Role.AUDITOR]))
require_any_role = Depends(require_role(Role.ALL_ROLES))
