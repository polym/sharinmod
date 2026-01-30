from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from api.models.shared_token import TokenVendor, TokenStatus


class SharedTokenCreate(BaseModel):
    """Schema for creating a shared token"""
    vendor: TokenVendor = Field(..., description="Token vendor (bigmodel or z.ai)")
    token: str = Field(..., description="Plain text token to share")
    token_metadata: Optional[str] = Field(None, max_length=1000, description="Optional metadata as JSON string")
    
    class Config:
        schema_extra = {
            "example": {
                "vendor": "bigmodel",
                "token": "your-api-token-here",
                "token_metadata": '{"name": "My BigModel Token", "purpose": "Sharing"}'
            }
        }


class SharedTokenResponse(BaseModel):
    """Shared token response (never includes decrypted token)"""
    id: int
    vendor: TokenVendor
    status: TokenStatus
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    total_uses: int
    token_metadata: Optional[str]
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "vendor": "bigmodel",
                "status": "active",
                "created_at": "2026-01-29T10:00:00Z",
                "updated_at": "2026-01-29T10:00:00Z",
                "last_used_at": None,
                "total_uses": 0,
                "token_metadata": '{"name": "My BigModel Token"}'
            }
        }


class SharedTokenList(BaseModel):
    """List of shared tokens"""
    total: int
    items: List[SharedTokenResponse]
    
    class Config:
        schema_extra = {
            "example": {
                "total": 2,
                "items": [
                    {
                        "id": 1,
                        "vendor": "bigmodel",
                        "status": "active",
                        "created_at": "2026-01-29T10:00:00Z",
                        "updated_at": "2026-01-29T10:00:00Z",
                        "last_used_at": None,
                        "total_uses": 0,
                        "token_metadata": None
                    }
                ]
            }
        }
