"""Authentication service for user login and token generation"""
from typing import Tuple, Optional

from sqlmodel import Session

from api.models.user import User
from api.services.user_service import get_user_by_email
from api.utils.security import verify_password
from api.utils.jwt import create_access_token
from datetime import timedelta
from api.config import settings


def authenticate_user(db: Session, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """
    Authenticate user with email and password.

    Returns:
        (user, error_type) where error_type is:
          - None on success
          - "invalid_credentials" for wrong email/password
          - "email_not_verified" if the account email has not been verified yet
    """
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None, "invalid_credentials"
    if not user.email_verified:
        return None, "email_not_verified"
    return user, None


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
