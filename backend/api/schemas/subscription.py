"""
Schemas for Subscription model
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SubscriptionResponse(BaseModel):
    """Subscription response model"""
    id: int
    model_id: str
    shared_api_key_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "model_id": "model-id-123",
                "shared_api_key_id": 5,
                "user_id": 10,
                "created_at": "2026-02-01T10:00:00Z"
            }
        }


class SubscriptionCreate(BaseModel):
    """Schema for creating a subscription (internal use)"""
    model_id: str
    shared_api_key_id: int
    user_id: int
