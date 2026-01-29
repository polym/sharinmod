"""
Token usage history schemas for API responses
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from api.models.token_usage import TokenAction


class TokenUsageHistoryResponse(BaseModel):
    """Single usage history record response"""
    id: int
    token_id: Optional[str] = None
    action: TokenAction
    timestamp: datetime
    details: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "token_id": "coding-token-123",
                "action": "consumed",
                "timestamp": "2026-01-29T10:30:00",
                "details": "Used for API calls to Coding service"
            }
        }
    }


class TokenUsageHistoryList(BaseModel):
    """Paginated list of usage history"""
    total: int
    page: int
    page_size: int
    items: List[TokenUsageHistoryResponse]


class TokenUsageStatistics(BaseModel):
    """User token usage statistics"""
    total_actions: int = Field(description="Total number of actions")
    tokens_shared: int = Field(description="Number of tokens shared")
    tokens_consumed: int = Field(description="Number of tokens consumed")
    tokens_generated: int = Field(description="Number of tokens generated")
    first_activity: Optional[datetime] = Field(None, description="First activity timestamp")
    last_activity: Optional[datetime] = Field(None, description="Most recent activity timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_actions": 42,
                "tokens_shared": 5,
                "tokens_consumed": 30,
                "tokens_generated": 7,
                "first_activity": "2026-01-15T08:00:00",
                "last_activity": "2026-01-29T14:30:00"
            }
        }
    }
