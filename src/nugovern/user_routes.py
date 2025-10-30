"""
user_routes.py

User management routes for eBIOS v1.0.0

Provides CRUD operations for user management (admin only)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional

from .auth import User, Role, get_current_user, require_role
from .user_db import get_user_db


# Request/Response models
class CreateUserRequest(BaseModel):
    """Request to create a new user"""
    username: str
    password: str
    role: str
    disabled: bool = False


class UpdateUserRequest(BaseModel):
    """Request to update user properties"""
    role: Optional[str] = None
    disabled: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    """Request to change user password"""
    new_password: str


class UserResponse(BaseModel):
    """User response (without password)"""
    username: str
    role: str
    disabled: bool


# Create router
router = APIRouter(prefix="/users")


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_role([Role.ADMIN]))
):
    """
    Create a new user (admin only)

    Args:
        request: User creation request
        current_user: Current authenticated admin user

    Returns:
        Created user

    Raises:
        HTTPException: If user already exists or invalid role
    """
    db = get_user_db()

    # Validate role
    if request.role not in Role.ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {Role.ALL_ROLES}"
        )

    # Check if user exists
    existing = db.get_user(request.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User '{request.username}' already exists"
        )

    # Create user
    user = db.create_user(
        username=request.username,
        password=request.password,
        role=request.role,
        disabled=request.disabled
    )

    return UserResponse(
        username=user.username,
        role=user.role,
        disabled=user.disabled
    )


@router.get("", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_role([Role.ADMIN]))
):
    """
    List all users (admin only)

    Args:
        current_user: Current authenticated admin user

    Returns:
        List of all users
    """
    db = get_user_db()
    users = db.list_users()

    return [
        UserResponse(
            username=user.username,
            role=user.role,
            disabled=user.disabled
        )
        for user in users
    ]


@router.get("/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    current_user: User = Depends(require_role([Role.ADMIN]))
):
    """
    Get user by username (admin only)

    Args:
        username: Username to retrieve
        current_user: Current authenticated admin user

    Returns:
        User details

    Raises:
        HTTPException: If user not found
    """
    db = get_user_db()
    user = db.get_user(username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    return UserResponse(
        username=user.username,
        role=user.role,
        disabled=user.disabled
    )


@router.put("/{username}", response_model=UserResponse)
async def update_user(
    username: str,
    request: UpdateUserRequest,
    current_user: User = Depends(require_role([Role.ADMIN]))
):
    """
    Update user properties (admin only)

    Args:
        username: Username to update
        request: Update request
        current_user: Current authenticated admin user

    Returns:
        Updated user

    Raises:
        HTTPException: If user not found or invalid role
    """
    db = get_user_db()

    # Validate role if provided
    if request.role and request.role not in Role.ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {Role.ALL_ROLES}"
        )

    # Update user
    user = db.update_user(
        username=username,
        role=request.role,
        disabled=request.disabled
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    return UserResponse(
        username=user.username,
        role=user.role,
        disabled=user.disabled
    )


@router.put("/{username}/password")
async def change_password(
    username: str,
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Change user password

    Users can change their own password.
    Admins can change any user's password.

    Args:
        username: Username to update
        request: Password change request
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or insufficient permissions
    """
    db = get_user_db()

    # Check permissions: user can change their own password, or admin can change any
    if username != current_user.username and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to change this user's password"
        )

    # Update password
    user = db.update_password(username, request.new_password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    return {"message": f"Password updated successfully for user '{username}'"}


@router.delete("/{username}")
async def delete_user(
    username: str,
    current_user: User = Depends(require_role([Role.ADMIN]))
):
    """
    Delete user (admin only)

    Args:
        username: Username to delete
        current_user: Current authenticated admin user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or trying to delete self
    """
    db = get_user_db()

    # Prevent admin from deleting themselves
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own user account"
        )

    # Delete user
    deleted = db.delete_user(username)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    return {"message": f"User '{username}' deleted successfully"}
