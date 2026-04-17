"""
Organization model for private workspace management
"""
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime, BigInteger


class Organization(SQLModel, table=True):
    """
    Organization model representing private workspaces

    Attributes:
        id: Primary key, auto-incremented
        name: Display name of the organization
        slug: Unique identifier for the organization (URL-friendly)
        created_at: Timestamp when organization was created
        updated_at: Timestamp when organization was last updated
    """
    __tablename__ = "organizations"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    slug: str = Field(unique=True, index=True, max_length=100)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    default_daily_token_limit: Optional[int] = Field(
        default=None,
        sa_type=BigInteger(),
        description="Default daily token limit for API keys in this organization"
    )
    is_personal: bool = Field(default=False, description="Whether this is a personal organization auto-created for the user")