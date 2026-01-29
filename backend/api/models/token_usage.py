"""
Token usage history model for tracking user activity
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class TokenAction(str, Enum):
    """Enum for token usage actions"""
    SHARED = "shared"           # User shared a token
    CONSUMED = "consumed"       # User consumed a shared token
    GENERATED = "generated"     # Platform generated token for user
    REVOKED = "revoked"         # Token was revoked
    SWITCHED = "switched"       # Auto-switched to different token


class TokenUsageHistory(SQLModel, table=True):
    """
    Token usage history for tracking user activity
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        token_id: Identifier of the token (may be external or internal)
        action: Type of action performed (shared, consumed, etc.)
        timestamp: When the action occurred
        details: JSON string with additional context
    """
    __tablename__ = "token_usage_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token_id: Optional[str] = Field(default=None, max_length=255, index=True)
    action: TokenAction = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    details: Optional[str] = Field(default=None)  # JSON string for flexibility
