"""
Schemas for LiteLLM callback webhooks
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class LiteLLMCallbackRequest(BaseModel):
    """
    Schema for LiteLLM success callback webhook

    LiteLLM sends a POST request with usage data after successful API calls.
    Key fields:
    - user_api_key_hash: Hash of the unified API key used by the consumer
    - model_id: LiteLLM model identifier (maps to Subscription)
    - total_tokens: Total tokens consumed in this request
    """
    # Core identification fields
    user_api_key_hash: str = Field(..., description="Hash of the user's unified API key")
    model_id: str = Field(..., description="LiteLLM model identifier")

    # Token usage
    total_tokens: int = Field(..., gt=0, le=1000000, description="Total tokens consumed in this request (must be positive, max 1M)")

    # Additional metadata
    start_time: Optional[str] = Field(None, description="Request start timestamp")
    end_time: Optional[str] = Field(None, description="Request end timestamp")

    # Raw data for debugging/extension
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw callback data for debugging")

    class Config:
        schema_extra = {
            "example": {
                "user_api_key_hash": "a1b2c3d4e5f6",
                "model_id": "model-id-123",
                "total_tokens": 1500,
                "start_time": "2026-02-01T10:00:00Z",
                "end_time": "2026-02-01T10:00:05Z"
            }
        }


class WebhookResponse(BaseModel):
    """Standard webhook response"""
    success: bool = True
    message: str = "Callback received"

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Callback received"
            }
        }
