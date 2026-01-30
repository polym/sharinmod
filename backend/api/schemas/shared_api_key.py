from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from api.models.shared_api_key import APIKeyProvider, APIKeyStatus


class SharedAPIKeyCreate(BaseModel):
    """Schema for creating a shared API key"""
    provider: APIKeyProvider = Field(..., description="API key provider (bigmodel or z.ai)")
    api_key: str = Field(..., description="Plain text API key to share")
    api_key_metadata: Optional[str] = Field(None, max_length=1000, description="Optional metadata as JSON string")
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "bigmodel",
                "api_key": "your-api-key-here",
                "api_key_metadata": '{"name": "My BigModel API Key", "purpose": "Sharing"}'
            }
        }


class SharedAPIKeyResponse(BaseModel):
    """Shared API key response (never includes decrypted API key)"""
    id: int
    provider: APIKeyProvider
    status: APIKeyStatus
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    total_uses: int
    api_key_metadata: Optional[str]
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "provider": "bigmodel",
                "status": "active",
                "created_at": "2026-01-29T10:00:00Z",
                "updated_at": "2026-01-29T10:00:00Z",
                "last_used_at": None,
                "total_uses": 0,
                "api_key_metadata": '{"name": "My BigModel API Key"}'
            }
        }


class SharedAPIKeyList(BaseModel):
    """List of shared API keys"""
    total: int
    items: List[SharedAPIKeyResponse]
    
    class Config:
        schema_extra = {
            "example": {
                "total": 2,
                "items": [
                    {
                        "id": 1,
                        "provider": "bigmodel",
                        "status": "active",
                        "created_at": "2026-01-29T10:00:00Z",
                        "updated_at": "2026-01-29T10:00:00Z",
                        "last_used_at": None,
                        "total_uses": 0,
                        "api_key_metadata": None
                    }
                ]
            }
        }
