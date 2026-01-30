"""
User schemas for API request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class UserCreate(BaseModel):
    """
    Schema for user registration request
    
    Validates:
    - Email format (RFC 5322 compliant)
    - Password strength (min 8 chars, max 72 for bcrypt, must have uppercase, lowercase, digit, special char)
    """
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    
    @field_validator('password')
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


class UserResponse(BaseModel):
    """
    Schema for user data in API responses
    
    Excludes sensitive fields like password/hashed_password
    """
    id: int
    email: str
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile (partial updates allowed)"""
    name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=500)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "张三",
                "avatar_url": "https://example.com/avatar.jpg",
                "bio": "全栈开发者，喜欢分享API额度"
            }
        }
    }


class UserProfileResponse(BaseModel):
    """Complete user profile response"""
    id: int
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }