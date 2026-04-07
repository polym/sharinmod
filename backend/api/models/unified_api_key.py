"""
Unified API Key model for platform-generated API access keys
"""
from sqlmodel import SQLModel, Field, Index, Relationship
from datetime import datetime, date
from typing import Optional, List
from enum import Enum


class UnifiedAPIKeyStatus(str, Enum):
    """Unified API key status"""
    ACTIVE = "active"
    REVOKED = "revoked"
    DAILY_LIMIT_EXCEEDED = "daily_limit_exceeded"


class UnifiedAPIKey(SQLModel, table=True):
    """
    Platform-generated unified API keys for accessing shared resources
    
    Business Rules:
    - Maximum 5 ACTIVE API keys per user
    - API key is 32-byte random string (URL-safe base64)
    - Cannot be regenerated after revocation
    """
    __tablename__ = "unified_api_keys"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    api_key: str = Field(unique=True, max_length=64)  # 32 bytes base64 = ~44 chars
    status: UnifiedAPIKeyStatus = Field(default=UnifiedAPIKeyStatus.ACTIVE)
    api_key_name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    litellm_key: Optional[str] = Field(default=None, max_length=255)  # Full LiteLLM API key
    api_key_hash: Optional[str] = Field(default=None, max_length=255, index=True)  # Token ID from LiteLLM for callback matching
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = Field(default=None)
    last_used_at: Optional[datetime] = Field(default=None)
    is_auto_created: bool = Field(default=False, description="Auto-created for claw, not counted in user quota")
    organization_id: Optional[int] = Field(default=None, index=True, foreign_key="organizations.id", description="Organization ID for private server isolation. None = public area.")

    # Daily token limit fields
    daily_token_limit: Optional[int] = Field(default=None, description="Daily token limit for this API key")
    daily_tokens_used: int = Field(default=0, description="Tokens used today")
    last_reset_date: Optional[date] = Field(default=None, description="Last date when daily tokens were reset")
    
    # Index for user + status queries (enforcing 5-key limit)
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
    )

    # Relationships
    limit_history: List["APIKeyLimitHistory"] = Relationship(
        back_populates="unified_api_key"
    )
