"""
API key usage history schemas for API responses
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from api.models.api_key_usage import APIKeyAction


class APIKeyUsageHistoryResponse(BaseModel):
    """Single usage history record response"""
    id: int
    api_key_id: Optional[str] = None
    action: APIKeyAction
    timestamp: datetime
    details: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "api_key_id": "coding-api-key-123",
                "action": "consumed",
                "timestamp": "2026-01-29T10:30:00",
                "details": "Used for API calls to Coding service"
            }
        }
    }


class APIKeyUsageHistoryList(BaseModel):
    """Paginated list of usage history"""
    total: int
    page: int
    page_size: int
    items: List[APIKeyUsageHistoryResponse]


class APIKeyUsageStatistics(BaseModel):
    """User API key usage statistics"""
    total_actions: int = Field(description="Total number of actions")
    api_keys_shared: int = Field(description="Number of API keys shared")
    api_keys_consumed: int = Field(description="Number of API keys consumed")
    api_keys_generated: int = Field(description="Number of API keys generated")
    first_activity: Optional[datetime] = Field(None, description="First activity timestamp")
    last_activity: Optional[datetime] = Field(None, description="Most recent activity timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_actions": 42,
                "api_keys_shared": 5,
                "api_keys_consumed": 30,
                "api_keys_generated": 7,
                "first_activity": "2026-01-15T08:00:00",
                "last_activity": "2026-01-29T14:30:00"
            }
        }
    }
