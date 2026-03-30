"""
Operation log model for tracking admin operations
"""
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum


class OperationType(str, Enum):
    """Enum for operation types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESTART = "restart"
    ENABLE = "enable"
    DISABLE = "disable"
    RESET_PASSWORD = "reset_password"
    GRANT_ADMIN = "grant_admin"
    REVOKE_ADMIN = "revoke_admin"
    RESET_TOKEN = "reset_token"


class ResourceType(str, Enum):
    """Enum for resource types"""
    USER = "user"
    CLAW = "claw"
    PROVIDER = "provider"
    PROVIDER_MODEL = "provider_model"
    UNIFIED_API_KEY = "unified_api_key"
    SHARED_API_KEY = "shared_api_key"
    GLOBAL_MODEL = "global_model"
    SYSTEM_SETTING = "system_setting"


class OperationLog(SQLModel, table=True):
    """
    Operation log for tracking all non-read operations on the platform

    Attributes:
        id: Primary key
        user_id: Foreign key to users table - ID of the user who performed the operation
        operation_type: Type of operation performed
        resource_type: Type of resource affected
        resource_id: ID of the affected resource
        created_at: When the operation was performed
    """
    __tablename__ = "operation_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    operation_type: OperationType = Field(index=True)
    resource_type: ResourceType = Field(index=True)
    resource_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
