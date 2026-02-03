"""
Schemas for LiteLLM callback webhooks

Based on LiteLLM callback structure:
http://bigfile.b0.upaiyun.com/litellm/2026-01-19/time-07-54-11-711881_chatcmpl-bf686de4af7d3a5a.json
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class LiteLLMMetadata(BaseModel):
    """Metadata from LiteLLM callback"""
    user_api_key_hash: Optional[str] = Field(None, alias="user_api_key_hash")
    user_api_key_alias: Optional[str] = None
    user_api_key_team_id: Optional[str] = None
    user_api_key_user_id: Optional[str] = None


class LiteLLMStatusFields(BaseModel):
    """Status fields from LiteLLM callback"""
    llm_api_status: Optional[str] = None
    guardrail_status: Optional[str] = None


class LiteLLMUsageObject(BaseModel):
    """Token usage details"""
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    completion_tokens_details: Optional[Dict[str, Any]] = None
    prompt_tokens_details: Optional[Dict[str, Any]] = None


class LiteLLMCostBreakdown(BaseModel):
    """Cost breakdown details"""
    input_cost: float
    output_cost: float
    total_cost: float
    tool_usage_cost: float = 0.0
    original_cost: float = 0.0


class LiteLLMHiddenParams(BaseModel):
    """Hidden parameters from callback"""
    model_id: Optional[str] = None
    cache_key: Optional[str] = None
    api_base: Optional[str] = None
    response_cost: Optional[float] = None
    litellm_overhead_time_ms: Optional[float] = None
    litellm_model_name: Optional[str] = None


class LiteLLMCallbackRequest(BaseModel):
    """
    Schema for LiteLLM success callback webhook

    This schema matches the actual LiteLLM callback structure.
    Key extraction happens in service layer.
    """
    # Core identification
    id: str = Field(..., description="Chat completion ID")
    trace_id: str = Field(..., description="Trace ID for request tracking")
    call_type: str = Field(default="acompletion", description="Type of call (acompletion, etc)")

    # Request flags
    cache_hit: Optional[bool] = Field(default=False, description="Whether cache was hit")
    stream: Optional[bool] = Field(default=False, description="Whether request was streamed")

    # Status
    status: str = Field(default="success", description="Request status")
    status_fields: Optional[LiteLLMStatusFields] = Field(None, description="Detailed status info")

    # Provider info
    custom_llm_provider: str = Field(..., description="LLM provider (openai, anthropic, etc)")

    # Timing - Support both snake_case (actual LiteLLM format) and camelCase
    start_time: float = Field(..., alias="startTime", description="Request start timestamp (Unix)")
    end_time: float = Field(..., alias="endTime", description="Request end timestamp (Unix)")
    completion_start_time: Optional[float] = Field(None, alias="completionStartTime", description="Completion start timestamp")
    response_time: float = Field(..., description="Response time in seconds")

    # Model info
    model: str = Field(..., description="Model name used")
    model_group: Optional[str] = Field(None, description="Model group name")
    model_id: Optional[str] = Field(None, description="Model ID (may be in hidden_params)")
    model_parameters: Optional[Dict[str, Any]] = Field(None, alias="model_parameters", description="Request parameters")
    hidden_params: Optional[LiteLLMHiddenParams] = Field(None, alias="hidden_params", description="Hidden parameters")

    # Token usage (at root level)
    total_tokens: int = Field(..., gt=0, le=1000000, description="Total tokens consumed")
    prompt_tokens: int = Field(..., ge=0, description="Prompt tokens used")
    completion_tokens: int = Field(..., ge=0, description="Completion tokens generated")

    # Cost info
    response_cost: float = Field(default=0.0, description="Response cost")
    cost_breakdown: Optional[LiteLLMCostBreakdown] = Field(None, description="Detailed cost breakdown")

    # Metadata (contains user_api_key_hash)
    metadata: Optional[LiteLLMMetadata] = Field(None, description="Request metadata including API key info")

    # Request details
    messages: Optional[list] = Field(None, description="Request messages")
    api_base: Optional[str] = Field(None, alias="api_base", description="API base URL")
    end_user: Optional[str] = Field("", description="End user identifier")

    # Response object
    response: Optional[Dict[str, Any]] = Field(None, description="Full response from LLM")

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
        "json_schema_extra": {
            "example": {
                "id": "chatcmpl-bf686de4af7d3a5a",
                "trace_id": "7fdc164c-3d33-4dee-a474-e1b643cb060d",
                "call_type": "acompletion",
                "cache_hit": False,
                "stream": True,
                "status": "success",
                "custom_llm_provider": "openai",
                "start_time": 1768809251.711881,
                "end_time": 1768809253.019879,
                "response_time": 0.19952106475830078,
                "model": "openai/Qwen/Qwen2.5-3B-Instruct",
                "model_id": "2c1f19ddf8b4ba01be63d045954aaeb5146de38cad44bb08391069bfc32b4108",
                "total_tokens": 173,
                "prompt_tokens": 33,
                "completion_tokens": 140,
                "response_cost": 0.0,
                "metadata": {
                    "user_api_key_hash": "986b30235724d09a7e4c57db0e136b29a2c8bd55bae9a1ddc4aa1c8da01586ca"
                }
            }
        }
    }


class WebhookResponse(BaseModel):
    """Standard webhook response"""
    success: bool = True
    message: str = "Callback received"

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Callback received"
            }
        }
    }


class LiteLLMFailureCallbackRequest(BaseModel):
    """
    Schema for LiteLLM failure callback webhook

    Failure callbacks may have missing token data and different structure
    than success callbacks. Most fields are optional.
    """
    # Core identification
    id: Optional[str] = Field(None, description="Chat completion ID (may be None)")
    trace_id: Optional[str] = Field(None, description="Trace ID for request tracking")

    # Status
    status: str = Field(default="failure", description="Request status")
    error_message: Optional[str] = Field(None, description="Error message if available")

    # Provider info
    custom_llm_provider: Optional[str] = Field(None, description="LLM provider (openai, anthropic, etc)")

    # Timing
    start_time: Optional[float] = Field(None, alias="startTime", description="Request start timestamp (Unix)")
    end_time: Optional[float] = Field(None, alias="endTime", description="Request end timestamp (Unix)")
    response_time: Optional[float] = Field(None, description="Response time in seconds")

    # Model info
    model: Optional[str] = Field(None, description="Model name used")
    model_id: Optional[str] = Field(None, description="Model ID (may be in hidden_params)")
    hidden_params: Optional[LiteLLMHiddenParams] = Field(None, alias="hidden_params", description="Hidden parameters")

    # Token usage (may be 0 or missing for failures)
    total_tokens: Optional[int] = Field(None, ge=0, description="Total tokens consumed (may be 0)")
    prompt_tokens: Optional[int] = Field(None, ge=0, description="Prompt tokens used (may be 0)")
    completion_tokens: Optional[int] = Field(None, ge=0, description="Completion tokens generated (may be 0)")

    # Metadata (contains user_api_key_hash)
    metadata: Optional[LiteLLMMetadata] = Field(None, description="Request metadata including API key info")

    # Additional error details
    exception: Optional[str] = Field(None, description="Exception type")
    error_code: Optional[str] = Field(None, description="Error code")

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
        "json_schema_extra": {
            "example": {
                "id": "chatcmpl-xyz",
                "trace_id": "7fdc164c-3d33-4dee-a474-e1b643cb060d",
                "status": "failure",
                "error_message": "Rate limit exceeded",
                "custom_llm_provider": "openai",
                "model": "openai/Qwen/Qwen2.5-3B-Instruct",
                "model_id": "2c1f19ddf8b4ba01be63d045954aaeb5146de38cad44bb08391069bfc32b4108",
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "error_code": "rate_limit_exceeded"
            }
        }
    }
