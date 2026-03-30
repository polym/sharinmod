"""
Operation log schemas for API responses
"""
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime
from datetime import timezone as dt_timezone
from typing import Optional, List
from api.models.operation_log import OperationType, ResourceType


class OperationLogResponse(BaseModel):
    """Single operation log record response"""
    id: int
    user_id: int
    operation_type: OperationType
    resource_type: ResourceType
    resource_id: int
    created_at: datetime

    @field_serializer('created_at')
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
                "operation_type": "create",
                "resource_type": "user",
                "resource_id": 5,
                "created_at": "2026-03-30T10:30:00+00:00"
            }
        }
    }


class OperationLogList(BaseModel):
    """Paginated list of operation logs"""
    total: int
    page: int
    page_size: int
    items: List[OperationLogResponse]


class OperationLogDetail(BaseModel):
    """Single operation log record with user details for display"""
    id: int
    user_id: int
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    operation_type: OperationType
    resource_type: ResourceType
    resource_id: int
    created_at: datetime

    @field_serializer('created_at')
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
                "user_email": "admin@example.com",
                "user_name": "Admin User",
                "operation_type": "create",
                "resource_type": "user",
                "resource_id": 5,
                "created_at": "2026-03-30T10:30:00+00:00"
            }
        }
    }


class OperationLogDetailList(BaseModel):
    """Paginated list of operation logs with user details"""
    total: int
    page: int
    page_size: int
    items: List[OperationLogDetail]
