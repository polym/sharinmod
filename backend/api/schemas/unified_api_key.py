"""
Pydantic schemas for unified API key endpoints
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
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
    
    class Config:
        from_attributes = True


class UnifiedAPIKeyUpdate(BaseModel):
    """Request schema for updating unified API key"""
    api_key_name: Optional[str] = Field(None, max_length=100, description="Updated name for the API key")
    description: Optional[str] = Field(None, max_length=500, description="Updated description for the API key. Should not contain sensitive information.")
    status: Optional[UnifiedAPIKeyStatus] = Field(None, description="Updated status for the API key")
    
    @validator('description')
    def validate_description(cls, v):
        if v and ('<' in v or '>' in v or 'script' in v.lower()):
            raise ValueError('Description contains potentially unsafe characters')
        return v


class UnifiedAPIKeyList(BaseModel):
    """List of unified API keys with pagination info"""
    total: int
    items: List[UnifiedAPIKeyResponse]
