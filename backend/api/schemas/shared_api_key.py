from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from api.models.shared_api_key import APIKeyProvider, APIKeyStatus


class SharedAPIKeyCreate(BaseModel):
    """Schema for creating a shared API key"""
    provider: APIKeyProvider = Field(..., description="API key provider (bigmodel or z.ai)")
    api_key: str = Field(..., description="Plain text API key to share")
    api_key_metadata: Optional[str] = Field(None, max_length=1000, description="Optional metadata as JSON string")
    selected_models: Optional[List[str]] = Field(None, description="List of models to bind (if None, bind all supported models)")

    class Config:
        schema_extra = {
            "example": {
                "provider": "bigmodel",
                "api_key": "your-api-key-here",
                "api_key_metadata": '{"name": "My BigModel API Key", "purpose": "Sharing"}',
                "selected_models": ["glm-4.7", "glm-4.6"]
            }
        }


class SharedAPIKeyUpdate(BaseModel):
    """Schema for updating a shared API key"""
    api_key: Optional[str] = Field(None, description="New API key to replace the existing one")
    selected_models: List[str] = Field(..., description="List of models to bind")

    class Config:
        schema_extra = {
            "example": {
                "api_key": "new-api-key-here",
                "selected_models": ["glm-4.7", "glm-4.5-air"]
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
    # Extended provider info fields
    supported_models: Optional[List[str]] = Field(None, description="List of supported models for this provider")
    provider_website: Optional[str] = Field(None, description="Provider official website URL")
    provider_display_name: Optional[str] = Field(None, description="Provider display name (e.g., '智谱AI')")
    provider_logo_path: Optional[str] = Field(None, description="Path to provider logo in frontend")
    
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
                "api_key_metadata": '{"name": "My BigModel API Key"}',
                "supported_models": ["glm-4.7", "glm-4.6", "glm-4.5-air"],
                "provider_website": "https://bigmodel.cn",
                "provider_display_name": "智谱 AI Coding Plan",
                "provider_logo_path": "/providers/bigmodel-logo.png"
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


class ChartDataPoint(BaseModel):
    """Single data point for usage chart"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    value: int = Field(..., description="Token usage value for that day")


class SharedAPIKeyMetrics(BaseModel):
    """Metrics and usage data for a shared API key"""
    total_tokens: float = Field(..., description="Total tokens consumed (in millions)")
    total_duration_days: float = Field(..., description="Total active duration in days")
    total_requests: int = Field(..., description="Total number of requests")
    chart_data: List[ChartDataPoint] = Field(..., description="14-day chart data")
    
    class Config:
        schema_extra = {
            "example": {
                "total_tokens": 592.5,
                "total_duration_days": 2.5,
                "total_requests": 45,
                "chart_data": [
                    {"date": "2026-01-18", "value": 50},
                    {"date": "2026-01-19", "value": 80}
                ]
            }
        }
