"""
User API routes for registration and authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session
from api.database import get_db
from api.schemas.user import UserResponse, UserProfileUpdate, UserProfileResponse
from api.services.user_service import update_user_profile, get_user_profile, change_password
from api.dependencies.auth import get_current_user
from api.models.user import User
import re

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    Requires valid JWT token in Authorization header
    """
    return current_user

@router.get("/me/profile", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's complete profile
    Requires JWT authentication
    """
    profile = get_user_profile(current_user)
    return profile


@router.patch("/me/profile", response_model=UserProfileResponse)
def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile (partial updates supported)
    Requires JWT authentication

    Only provided fields will be updated (PATCH semantics)
    """
    updated_user = update_user_profile(db, current_user, profile_data)
    return updated_user


class ChangePasswordRequest(BaseModel):
    """Schema for password change request"""
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets security requirements:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        return v


@router.patch("/me/password")
def change_my_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password

    After successful password change, the force_password_change flag will be cleared.
    Requires JWT authentication.

    Password requirements:
    - Minimum 8 characters, maximum 72 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    change_password(db, current_user, request.new_password)
    return {"message": "密码修改成功"}