"""
Email verification token model for confirming user email addresses
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime


class EmailVerificationToken(SQLModel, table=True):
    """
    One-time token sent to users to verify their email address.

    Attributes:
        id: Primary key
        token: Unique URL-safe token, indexed for fast lookups
        user_id: Foreign key to users table
        expires_at: Token expiration timestamp (24 hours after creation)
        is_used: Whether this token has already been consumed
    """
    __tablename__ = "email_verification_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True, max_length=255)
    user_id: int = Field(foreign_key="users.id")
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    is_used: bool = Field(default=False)
