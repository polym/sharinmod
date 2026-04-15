"""
Password reset token model for secure password management
"""
from sqlmodel import SQLModel, Field, ForeignKey
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime


class PasswordResetToken(SQLModel, table=True):
    """
    Password reset token model for secure password management

    Attributes:
        id: Primary key, auto-incremented
        token: Unique reset token, indexed for fast lookups
        user_id: Foreign key reference to User
        expires_at: Token expiration timestamp
        is_used: Whether token has been used
    """
    __tablename__ = "password_reset_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True, max_length=255)
    user_id: int = Field(foreign_key="users.id")
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    is_used: bool = Field(default=False)
