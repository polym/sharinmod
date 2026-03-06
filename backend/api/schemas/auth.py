"""Authentication schemas for login requests and responses"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from .user import UserResponse


class UserLogin(BaseModel):
    """Schema for user login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None
    force_password_change: bool = False
