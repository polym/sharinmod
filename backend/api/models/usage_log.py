"""
Usage log model for tracking API call usage details
"""
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class UsageLogStatus(str, Enum):
    """Enum for usage log status"""
    SUCCESS = "success"
    FAILURE = "failure"


class UsageLog(SQLModel, table=True):
    """
    Usage log for tracking API call usage details

    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        unified_api_key_id: Foreign key to unified_api_keys table (nullable)
        unified_api_key_name: Name of the API key used (nullable)
        model_id: Model identifier from LiteLLM (nullable)
        model_name: Model name used
        status: Status of the call (success/failure)
        total_duration: Total response time in seconds (nullable)
        ttft: Time to first token in seconds (nullable)
        subscription_id: Foreign key to subscriptions table (nullable)
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens
        total_tokens: Total tokens consumed
        request_time: When the API call was made
        created_at: When the log entry was created
    """
    __tablename__ = "usage_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    unified_api_key_id: Optional[int] = Field(default=None, foreign_key="unified_api_keys.id")
    unified_api_key_name: Optional[str] = Field(default=None, max_length=255)
    model_id: Optional[str] = Field(default=None, max_length=255)
    model_name: str = Field(max_length=255)
    status: UsageLogStatus = Field(index=True)
    total_duration: Optional[float] = Field(default=None)
    ttft: Optional[float] = Field(default=None)
    subscription_id: Optional[int] = Field(default=None, foreign_key="subscriptions.id")
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    request_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
