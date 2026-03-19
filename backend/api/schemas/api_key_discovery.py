from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class APIKeyDiscoveryItem(BaseModel):
    """
    Shared API key information for discovery (no sensitive data)

    Excludes actual API key value and owner's identity details
    Shows only what consumers need to see
    """
    id: int = Field(description="API key ID for reference")
    provider: str = Field(description="API key provider (bigmodel, z.ai, volcengine, moonshot, minimax, openrouter, etc.)")
    provider_username: str = Field(description="Username of API key provider (email prefix)")
    shared_duration_days: int = Field(description="Days since API key was shared")
    total_uses: int = Field(description="Total number of times API key was used")
    created_at: datetime = Field(description="When API key was shared")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "provider": "bigmodel",
                "provider_username": "user123",
                "shared_duration_days": 15,
                "total_uses": 42,
                "created_at": "2026-01-15T10:00:00"
            }
        }


class APIKeyDiscoveryList(BaseModel):
    """Paginated list of discoverable API keys"""
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of available API keys")
    items: List[APIKeyDiscoveryItem] = Field(description="List of available API keys")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 10,
                "total": 25,
                "items": [
                    {
                        "id": 123,
                        "provider": "bigmodel",
                        "provider_username": "user123",
                        "shared_duration_days": 15,
                        "total_uses": 42,
                        "created_at": "2026-01-15T10:00:00"
                    }
                ]
            }
        }
