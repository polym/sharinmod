"""
User API routes for registration and authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from api.database import get_db
from api.schemas.user import UserCreate, UserResponse, UserProfileUpdate, UserProfileResponse
from api.services.user_service import create_user, update_user_profile, get_user_profile
from api.dependencies.auth import get_current_user
from api.models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password"
)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account
    
    **Requirements:**
    - Email must be valid and unique
    - Password must be at least 8 characters
    - Password must contain uppercase, lowercase, digit, and special character
    
    **Returns:**
    - 201: User created successfully
    - 409: Email already registered
    - 422: Validation error (invalid email or weak password)
    """
    try:
        user = create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


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