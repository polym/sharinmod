"""
Pydantic schemas for unified API key endpoints
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from api.models.unified_api_key import UnifiedAPIKeyStatus


class UnifiedAPIKeyGenerate(BaseModel):
    """Request schema for generating unified API key"""
    api_key_name: Optional[str] = Field(None, max_length=100, description="Optional user-friendly name for the API key")


class UnifiedAPIKeyResponse(BaseModel):
    """Response schema for unified API key"""
    id: int
    user_id: int
    api_key: str
    status: UnifiedAPIKeyStatus
    api_key_name: Optional[str]
    litellm_key: Optional[str]
    created_at: datetime
    revoked_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UnifiedAPIKeyList(BaseModel):
    """List of unified API keys with pagination info"""
    total: int
    items: List[UnifiedAPIKeyResponse]
