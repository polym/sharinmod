"""
User API routes for registration and authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from api.database import get_db
from api.schemas.user import UserResponse, UserProfileUpdate, UserProfileResponse
from api.services.user_service import update_user_profile, get_user_profile
from api.dependencies.auth import get_current_user
from api.models.user import User

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