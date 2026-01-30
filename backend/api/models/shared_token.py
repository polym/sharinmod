from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional
from enum import Enum


class TokenVendor(str, Enum):
    """Supported token vendors"""
    BIGMODEL = "bigmodel"      # 智谱AI - https://open.bigmodel.cn
    ZAI = "z.ai"               # Z.AI - https://z.ai


class TokenStatus(str, Enum):
    """Token sharing status"""
    ACTIVE = "active"           # Available for sharing
    INACTIVE = "inactive"       # Temporarily unavailable
    REVOKED = "revoked"         # Permanently revoked


class SharedToken(SQLModel, table=True):
    """
    Shared tokens stored securely with encryption
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table (token owner)
        vendor: Token vendor (bigmodel or z.ai)
        encrypted_token: AES-256 encrypted token value
        status: Current status (active, inactive, revoked)
        created_at: When token was shared
        updated_at: Last status update
        last_used_at: Last time token was used
        total_uses: Total number of times consumed
        token_metadata: JSON string with additional info (e.g., token name)
    """
    __tablename__ = "shared_tokens"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    vendor: TokenVendor = Field(index=True)
    encrypted_token: str = Field(max_length=500)  # Encrypted value
    status: TokenStatus = Field(default=TokenStatus.ACTIVE, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(default=None)
    total_uses: int = Field(default=0)
    token_metadata: Optional[str] = Field(default=None, max_length=1000)  # JSON string
    litellm_model_id: Optional[str] = Field(default=None, max_length=100)  # Model ID from LiteLLM
    
    # Unique constraint: one token per vendor per user
    __table_args__ = (
        Index("idx_user_vendor_unique", "user_id", "vendor", unique=True),
    )
