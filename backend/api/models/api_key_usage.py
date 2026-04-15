"""
API key usage history model for tracking user activity
"""
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from sqlalchemy import Column, DateTime


class APIKeyAction(str, Enum):
    """Enum for API key usage actions"""
    SHARED = "shared"           # User shared an API key
    CONSUMED = "consumed"       # User consumed a shared API key
    GENERATED = "generated"     # Platform generated API key for user
    REVOKED = "revoked"         # API key was revoked
    SWITCHED = "switched"       # Auto-switched to different API key


class APIKeyUsageHistory(SQLModel, table=True):
    """
    API key usage history for tracking user activity
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        api_key_id: Identifier of the API key (may be external or internal)
        action: Type of action performed (shared, consumed, etc.)
        timestamp: When the action occurred
        details: JSON string with additional context
    """
    __tablename__ = "api_key_usage_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    api_key_id: Optional[str] = Field(default=None, max_length=255, index=True)
    action: APIKeyAction = Field(index=True)
    timestamp: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    details: Optional[str] = Field(default=None)  # JSON string for flexibility
