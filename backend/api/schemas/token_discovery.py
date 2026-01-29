from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from api.models.shared_token import TokenVendor


class TokenDiscoveryItem(BaseModel):
    """
    Shared token information for discovery (no sensitive data)
    
    Excludes actual token value and token owner's identity details
    Shows only what consumers need to see
    """
    id: int = Field(description="Token ID for reference")
    vendor: TokenVendor = Field(description="Token vendor (bigmodel, z.ai)")
    provider_username: str = Field(description="Username of token provider (email prefix)")
    shared_duration_days: int = Field(description="Days since token was shared")
    total_uses: int = Field(description="Total number of times token was used")
    created_at: datetime = Field(description="When token was shared")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "vendor": "bigmodel",
                "provider_username": "user123",
                "shared_duration_days": 15,
                "total_uses": 42,
                "created_at": "2026-01-15T10:00:00"
            }
        }


class TokenDiscoveryList(BaseModel):
    """Paginated list of discoverable tokens"""
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of available tokens")
    items: List[TokenDiscoveryItem] = Field(description="List of available tokens")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 10,
                "total": 25,
                "items": [
                    {
                        "id": 123,
                        "vendor": "bigmodel",
                        "provider_username": "user123",
                        "shared_duration_days": 15,
                        "total_uses": 42,
                        "created_at": "2026-01-15T10:00:00"
                    }
                ]
            }
        }
