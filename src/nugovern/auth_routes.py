"""
auth_routes.py

Authentication endpoints for NUGovern API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from .auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    decode_token,
    LoginRequest,
    RefreshTokenRequest,
    Token,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest):
    """
    Login with username and password

    Returns JWT access and refresh tokens

    Default users:
    - admin/admin123 (full access)
    - operator/operator123 (operations + queries)
    - auditor/auditor123 (read-only)
    """
    user = authenticate_user(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )

    # Create refresh token
    refresh_token = create_refresh_token(
        data={"sub": user.username, "role": user.role}
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token

    Args:
        request: Refresh token request containing the refresh token

    Returns:
        New access and refresh tokens
    """
    try:
        token_data = decode_token(request.refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": token_data.username, "role": token_data.role},
        expires_delta=access_token_expires
    )

    new_refresh_token = create_refresh_token(
        data={"sub": token_data.username, "role": token_data.role}
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information

    Requires valid JWT token
    """
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout current user

    Note: JWT tokens are stateless, so logout is handled client-side
    by discarding the token. For production, implement token blacklist.
    """
    return {
        "message": "Successfully logged out",
        "username": current_user.username
    }
