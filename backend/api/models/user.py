"""
User model for authentication and user management
"""
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime


class User(SQLModel, table=True):
    """
    User model representing registered users in the system
    
    Attributes:
        id: Primary key, auto-incremented
        email: Unique email address, indexed for performance
        hashed_password: Bcrypt hashed password (never store plain text)
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        name: User's display name (optional)
        avatar_url: URL to user's avatar image (optional)
        bio: User's biography/description (optional)
    """
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: Optional[str] = Field(default=None, max_length=255)

    # OAuth fields
    oauth_provider: Optional[str] = Field(default=None, max_length=50)  # 'github', 'google', etc.
    oauth_provider_user_id: Optional[str] = Field(default=None, max_length=255)  # GitHub user ID, etc.

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Profile fields
    name: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    bio: Optional[str] = Field(default=None, max_length=500)

    # LiteLLM integration
    litellm_user_id: Optional[str] = Field(default=None, max_length=255)

    # Token statistics
    consumed_tokens: int = Field(default=0)  # Tokens consumed by this user
    contributed_tokens: int = Field(default=0)  # Tokens contributed by this user's shared API keys

    # Admin privileges
    is_admin: bool = Field(default=False, description="Whether user has admin privileges")

    # Password change requirement
    force_password_change: bool = Field(default=False, description="Whether user must change password on next login")

    # User status
    is_disabled: bool = Field(default=False, description="Whether user is disabled")
    deleted_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True),
        default=None,
        description="Soft delete timestamp"
    )
