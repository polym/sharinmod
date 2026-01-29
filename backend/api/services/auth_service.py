"""Authentication service for user login and token generation"""
from sqlmodel import Session
from api.models.user import User
from api.services.user_service import get_user_by_email
from api.utils.security import verify_password
from api.utils.jwt import create_access_token
from datetime import timedelta
from api.config import settings


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """
    Authenticate user with email and password
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
        
    Returns:
        User object if credentials are valid, None otherwise
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user_token(user: User) -> str:
    """
    Create access token for authenticated user
    
    Args:
        user: User object
        
    Returns:
        JWT access token string
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return access_token
