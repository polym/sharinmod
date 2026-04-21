from sqlmodel import SQLModel, Field, Index
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from sqlalchemy import Column, DateTime


class APIKeyStatus(str, Enum):
    """API key sharing status"""
    ACTIVE = "active"           # Available for sharing
    INACTIVE = "inactive"       # Temporarily unavailable
    REVOKED = "revoked"         # Permanently revoked


class SharedAPIKey(SQLModel, table=True):
    """
    Shared API keys stored securely with encryption
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table (API key owner)
        provider: API key provider (bigmodel or z.ai)
        encrypted_api_key: AES-256 encrypted API key value
        status: Current status (active, inactive, revoked)
        created_at: When API key was shared
        updated_at: Last status update
        last_used_at: Last time API key was used
        total_uses: Total number of times consumed
        api_key_metadata: JSON string with additional info (e.g., API key name)
        litellm_model_id: Model ID from LiteLLM
    """
    __tablename__ = "shared_api_keys"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    provider: str = Field(index=True, max_length=100)  # Changed from enum to str to support dynamic providers
    organization_id: Optional[int] = Field(default=None, index=True, foreign_key="organizations.id")
    encrypted_api_key: str = Field(max_length=500)  # Encrypted value
    status: APIKeyStatus = Field(default=APIKeyStatus.ACTIVE, index=True)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_used_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True),
        default=None
    )
    total_uses: int = Field(default=0)
    api_key_metadata: Optional[str] = Field(default=None, max_length=1000)  # JSON string
    litellm_model_id: Optional[str] = Field(default=None, max_length=100)  # Model ID from LiteLLM (deprecated, use litellm_model_ids)
    litellm_model_ids: Optional[str] = Field(default=None, max_length=1000)  # JSON string mapping model_name -> litellm_model_id
    user_selected_models: Optional[str] = Field(default=None, max_length=1000)  # JSON array of user-selected model keys; persisted through disable/enable cycles

    # Token statistics
    api_key_hash: Optional[str] = Field(default=None, max_length=255)  # LiteLLM token_id for identifying user API key in callbacks
    total_requests: int = Field(default=0)  # Total number of requests made using this shared API key
    total_tokens: int = Field(default=0)  # Total tokens consumed through this shared API key

    # Rate limit handling
    rate_limit_reset_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True, index=True),
        default=None,
        description="Rate limit reset time when API key exceeded quota"
    )
    rate_limit_models_backup: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Backup of user-selected models (JSON array) for recovery"
    )

    # Unique constraint: one API key per provider per user per organization
    __table_args__ = (
        Index("idx_user_provider_unique", "user_id", "provider", "organization_id", unique=True),
    )
