"""
Unified Token model for platform-generated API access tokens
"""
from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional
from enum import Enum


class UnifiedTokenStatus(str, Enum):
    """Unified token status"""
    ACTIVE = "active"
    REVOKED = "revoked"


class UnifiedToken(SQLModel, table=True):
    """
    Platform-generated unified tokens for accessing shared resources
    
    Business Rules:
    - Maximum 5 ACTIVE tokens per user
    - Token is 32-byte random string (URL-safe base64)
    - Cannot be regenerated after revocation
    """
    __tablename__ = "unified_tokens"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    token: str = Field(unique=True, max_length=64)  # 32 bytes base64 = ~44 chars
    status: UnifiedTokenStatus = Field(default=UnifiedTokenStatus.ACTIVE)
    token_name: Optional[str] = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = Field(default=None)
    
    # Index for user + status queries (enforcing 5-token limit)
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
    )
