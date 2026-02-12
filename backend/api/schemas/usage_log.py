"""
Usage log schemas for API responses
"""
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime, date, timezone
from typing import Optional, List
from api.models.usage_log import UsageLogKind


class UsageLogResponse(BaseModel):
    """Single usage log record response"""
    id: int
    user_id: int
    unified_api_key_id: Optional[int] = None
    unified_api_key_name: Optional[str] = None
    model_id: Optional[str] = None
    model_name: str
    status: str
    kind: UsageLogKind = Field(default=UsageLogKind.DIRECT, description="Who provided the API key (own/shared/direct)")
    client: Optional[str] = None
    total_duration: Optional[float] = None
    ttft: Optional[float] = None
    subscription_id: Optional[int] = None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_time: datetime
    created_at: datetime
    trace_id: Optional[str] = None
    num_fails: int = 0
    error_details: Optional[str] = None

    @field_serializer('request_time', 'created_at')
    def datetime_to_rfc3339(self, dt: datetime) -> str:
        """Serialize datetime to RFC3339 format with timezone suffix"""
        if dt.tzinfo is None:
            # If datetime is naive, assume UTC
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # If datetime has timezone, convert to UTC for consistency
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": 1,
                "unified_api_key_id": 1,
                "unified_api_key_name": "my-api-key",
                "model_id": "model_123",
                "model_name": "openai/gpt-4",
                "status": "success",
                "kind": "direct",
                "client": "Chrome",
                "total_duration": 0.5,
                "ttft": 0.3,
                "subscription_id": 1,
                "input_tokens": 33,
                "output_tokens": 140,
                "total_tokens": 173,
                "request_time": "2026-02-02T10:30:00+00:00",
                "created_at": "2026-02-02T10:30:00+00:00",
                "trace_id": "abc123",
                "num_fails": 0,
                "error_details": None
            }
        }
    }


class UsageLogList(BaseModel):
    """Paginated list of usage logs"""
    total: int
    page: int
    page_size: int
    items: List[UsageLogResponse]
    timezone: str = Field(default="Asia/Shanghai", description="Timezone used for date filtering")


class HourlyTokenData(BaseModel):
    """Hourly token distribution data"""
    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    tokens: int = Field(..., ge=0, description="Total tokens for this hour")


class UsageOverviewResponse(BaseModel):
    """Usage overview statistics for a specific date"""
    date: date
    total_requests: int = Field(description="Total number of requests")
    successful_requests: int = Field(description="Number of successful requests")
    failed_requests: int = Field(description="Number of failed requests")
    total_tokens: int = Field(description="Total tokens consumed")
    input_tokens: int = Field(description="Total input/prompt tokens")
    output_tokens: int = Field(description="Total output/completion tokens")
    hourly_distribution: List[HourlyTokenData] = Field(description="24-hour token distribution (hours 0-23)")
    timezone: str = Field(default="Asia/Shanghai", description="Timezone used for date filtering")

    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2026-02-02",
                "total_requests": 42,
                "successful_requests": 40,
                "failed_requests": 2,
                "total_tokens": 7266,
                "input_tokens": 1386,
                "output_tokens": 5880,
                "hourly_distribution": [
                    {"hour": 0, "tokens": 120},
                    {"hour": 1, "tokens": 0},
                    {"hour": 10, "tokens": 3500},
                    {"hour": 23, "tokens": 200}
                ]
            }
        }
    }
