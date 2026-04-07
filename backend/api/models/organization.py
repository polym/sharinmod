"""
Organization model for private workspace management
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)