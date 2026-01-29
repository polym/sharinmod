"""
User model for authentication and user management
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class User(SQLModel, table=True):
    """
    User model representing registered users in the system
    
    Attributes:
        id: Primary key, auto-incremented
        email: Unique email address, indexed for performance
        hashed_password: Bcrypt hashed password (never store plain text)
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
