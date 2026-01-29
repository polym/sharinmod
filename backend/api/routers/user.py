"""
User API routes for registration and authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from api.database import get_db
from api.schemas.user import UserCreate, UserResponse
from api.services.user_service import create_user

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
