"""
Pydantic schemas for unified API key endpoints
"""
from pydantic import BaseModel, Field, validator, computed_field
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Callable
from api.models.unified_api_key import UnifiedAPIKeyStatus


class UnifiedAPIKeyGenerate(BaseModel):
    """Request schema for generating unified API key"""
    api_key_name: Optional[str] = Field(None, max_length=100, description="Optional user-friendly name for the API key")
    description: Optional[str] = Field(None, max_length=500, description="Optional description for the API key. Should not contain sensitive information.")
    
    @validator('description')
    def validate_description(cls, v):
        if v and ('<' in v or '>' in v or 'script' in v.lower()):
            raise ValueError('Description contains potentially unsafe characters')
        return v


class UnifiedAPIKeyResponse(BaseModel):
    """Response schema for unified API key"""
    id: int
    user_id: int
    api_key: str
    status: UnifiedAPIKeyStatus
    api_key_name: Optional[str]
    description: Optional[str]
    litellm_key: Optional[str]
    created_at: datetime
    revoked_at: Optional[datetime]
    last_used_at: Optional[datetime]
    daily_token_limit: Optional[int]
    daily_tokens_used: int
    last_reset_date: Optional[date]

    @computed_field
    @property
    def daily_limit_exceeded(self) -> bool:
        """Check if daily limit is exceeded"""
        if self.daily_token_limit is None:
            return False
        return self.daily_tokens_used >= self.daily_token_limit

    class Config:
        from_attributes = True
        json_encoders: Dict[type, Callable] = {
            datetime: lambda v: v.isoformat() if v.tzinfo else v.replace(tzinfo=timezone.utc).isoformat(),
            date: lambda v: v.isoformat()
        }


class UnifiedAPIKeyUpdate(BaseModel):
    """Request schema for updating unified API key"""
    api_key_name: Optional[str] = Field(None, max_length=100, description="Updated name for the API key")
    description: Optional[str] = Field(None, max_length=500, description="Updated description for the API key. Should not contain sensitive information.")
    status: Optional[UnifiedAPIKeyStatus] = Field(None, description="Updated status for the API key")
    daily_token_limit: Optional[int] = Field(None, description="Daily token limit for this API key")
    
    @validator('description')
    def validate_description(cls, v):
        if v and ('<' in v or '>' in v or 'script' in v.lower()):
            raise ValueError('Description contains potentially unsafe characters')
        return v


class UnifiedAPIKeyList(BaseModel):
    """List of unified API keys with pagination info"""
    total: int
    items: List[UnifiedAPIKeyResponse]
