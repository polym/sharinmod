from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional
from enum import Enum


class APIKeyProvider(str, Enum):
    """Supported API key providers"""
    BIGMODEL = "bigmodel"      # 智谱AI - https://open.bigmodel.cn
    ZAI = "z.ai"               # Z.AI - https://z.ai


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
    provider: APIKeyProvider = Field(index=True)
    encrypted_api_key: str = Field(max_length=500)  # Encrypted value
    status: APIKeyStatus = Field(default=APIKeyStatus.ACTIVE, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(default=None)
    total_uses: int = Field(default=0)
    api_key_metadata: Optional[str] = Field(default=None, max_length=1000)  # JSON string
    litellm_model_id: Optional[str] = Field(default=None, max_length=100)  # Model ID from LiteLLM (deprecated, use litellm_model_ids)
    litellm_model_ids: Optional[str] = Field(default=None, max_length=1000)  # JSON string mapping model_name -> litellm_model_id

    # Token statistics
    api_key_hash: Optional[str] = Field(default=None, max_length=255)  # LiteLLM token_id for identifying user API key in callbacks
    total_requests: int = Field(default=0)  # Total number of requests made using this shared API key
    total_tokens: int = Field(default=0)  # Total tokens consumed through this shared API key
    
    # Unique constraint: one API key per provider per user
    __table_args__ = (
        Index("idx_user_provider_unique", "user_id", "provider", unique=True),
    )
