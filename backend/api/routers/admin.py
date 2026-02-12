"""
Admin router for administrative operations
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session
from typing import Annotated
from api.database import get_db
from api.dependencies.auth import require_admin
from api.services.user_service import get_all_users, grant_admin_privilege, revoke_admin_privilege
from api.schemas.user import UserResponse

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> list[UserResponse]:
    """
    Get all users (admin only)

    Args:
        offset: Number of users to skip (for pagination)
        limit: Maximum number of users to return
        db: Database session

    Returns:
        List of users
    """
    users = get_all_users(db, offset, limit)
    return [UserResponse.model_validate(u) for u in users]


@router.put("/users/{user_id}/grant-admin", response_model=UserResponse)
def grant_admin(
    user_id: int,
    current_admin: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Grant admin privileges to a user (admin only)

    Args:
        user_id: ID of the user to grant admin privileges
        current_admin: Current authenticated admin user
        db: Database session

    Returns:
        Updated user object
    """
    user = grant_admin_privilege(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}/revoke-admin", response_model=UserResponse)
def revoke_admin(
    user_id: int,
    current_admin: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Revoke admin privileges from a user (admin only)

    Args:
        user_id: ID of the user to revoke admin privileges
        current_admin: Current authenticated admin user
        db: Database session

    Returns:
        Updated user object
    """
    user = revoke_admin_privilege(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)
