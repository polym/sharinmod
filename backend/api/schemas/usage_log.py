"""
Usage log schemas for API responses
"""
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime, date as Date
from datetime import timezone as dt_timezone
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
    provider: Optional[str] = None
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
            dt = dt.replace(tzinfo=dt_timezone.utc)
        else:
            # If datetime has timezone, convert to UTC for consistency
            dt = dt.astimezone(dt_timezone.utc)
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
                "provider": "openai",
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


class QuarterHourlyTokenData(BaseModel):
    """Quarter-hourly token distribution data (15-minute intervals)"""
    quarter_hour: int = Field(..., ge=0, le=95, description="Quarter hour of day (0-95, each represents 15 minutes)")
    tokens: int = Field(..., ge=0, description="Total tokens for this 15-minute interval")


# Alias for backward compatibility
HourlyTokenData = QuarterHourlyTokenData


class UsageOverviewResponse(BaseModel):
    """Usage overview statistics for a specific date"""
    date: Date
    total_requests: int = Field(description="Total number of requests")
    successful_requests: int = Field(description="Number of successful requests")
    failed_requests: int = Field(description="Number of failed requests")
    total_tokens: int = Field(description="Total tokens consumed")
    input_tokens: int = Field(description="Total input/prompt tokens")
    output_tokens: int = Field(description="Total output/completion tokens")
    quarter_hourly_distribution: List[QuarterHourlyTokenData] = Field(description="96 quarter-hour token distribution (0-95, each represents 15 minutes)")
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
                "quarter_hourly_distribution": [
                    {"quarter_hour": 0, "tokens": 120},
                    {"quarter_hour": 1, "tokens": 0},
                    {"quarter_hour": 42, "tokens": 3500},
                    {"quarter_hour": 95, "tokens": 200}
                ]
            }
        }
    }


class DailyTrendData(BaseModel):
    """Daily token consumption trend data"""
    date: Date = Field(description="Date of the trend data point")
    total_tokens: int = Field(description="Total tokens consumed on this date")

    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2026-03-26",
                "total_tokens": 5000
            }
        }
    }


class UserRankingData(BaseModel):
    """User token consumption ranking data"""
    user_id: int = Field(description="User ID")
    consumed_tokens: int = Field(description="Total tokens consumed by this user")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "consumed_tokens": 10000
            }
        }
    }


class ModelUsageData(BaseModel):
    """Model token usage distribution data"""
    model_name: str = Field(description="Model name")
    total_tokens: int = Field(description="Total tokens consumed by this model")
    percentage: float = Field(description="Percentage of total tokens")

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_name": "gpt-4",
                "total_tokens": 5000,
                "percentage": 50.0
            }
        }
    }


class SystemOverviewResponse(BaseModel):
    """System-wide usage overview statistics"""
    total_tokens: int = Field(description="Total tokens consumed across all time")
    today_tokens: int = Field(description="Total tokens consumed today")
    user_count: int = Field(description="Total number of active users (excluding soft-deleted)")
    claw_count: int = Field(description="Total number of claw instances")
    daily_trends: List[DailyTrendData] = Field(description="Daily token consumption trends")
    user_rankings: List[UserRankingData] = Field(description="Top 10 users by token consumption")
    model_usage: List[ModelUsageData] = Field(description="Model token usage distribution")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_tokens": 100000,
                "today_tokens": 5000,
                "user_count": 50,
                "claw_count": 20,
                "daily_trends": [
                    {"date": "2026-03-26", "total_tokens": 5000},
                    {"date": "2026-03-25", "total_tokens": 4500}
                ],
                "user_rankings": [
                    {"user_id": 1, "consumed_tokens": 10000},
                    {"user_id": 2, "consumed_tokens": 8000}
                ],
                "model_usage": [
                    {"model_name": "gpt-4", "total_tokens": 50000, "percentage": 50.0},
                    {"model_name": "claude-3-opus", "total_tokens": 30000, "percentage": 30.0}
                ]
            }
        }
    }
