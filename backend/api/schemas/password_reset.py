"""
Password reset schemas for API request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class UserCreateRequest(BaseModel):
    """
    Schema for admin user creation request

    Only requires email, password will be set via reset token
    """
    email: EmailStr


class PasswordResetTokenResponse(BaseModel):
    """
    Schema for password reset token response

    Returns the secure token and reset link
    """
    token: str
    link: str
    expires_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SetPasswordRequest(BaseModel):
    """
    Schema for setting new password via reset token

    Validates password strength (min 8 chars, max 72 for bcrypt, must have uppercase, lowercase, digit, special char)
    """
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets security requirements:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('密码必须包含至少一个特殊字符')
        return v


class VerifyTokenResponse(BaseModel):
    """
    Schema for token verification response

    Returns user email if token is valid
    """
    email: str
    valid: bool