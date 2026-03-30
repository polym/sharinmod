"""
Operation log model for tracking admin operations
"""
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from enum import Enum
from sqlalchemy import Enum as SQLEnum, Column, Integer, DateTime, ForeignKey, String


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
        resource_name: Name of the affected resource (persisted even after resource is deleted)
        created_at: When the operation was performed
    """
    __tablename__ = "operation_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(
        sa_column=Column(Integer, ForeignKey("users.id"), nullable=False, index=True),
        default=None
    )
    operation_type: OperationType = Field(
        sa_column=Column(
            SQLEnum(
                OperationType,
                values_callable=lambda x: [e.value for e in x],
                name="operationtype"
            ),
            nullable=False,
            index=True
        )
    )
    resource_type: ResourceType = Field(
        sa_column=Column(
            SQLEnum(
                ResourceType,
                values_callable=lambda x: [e.value for e in x],
                name="resourcetype"
            ),
            nullable=False,
            index=True
        )
    )
    resource_id: int = Field(sa_column=Column(Integer, nullable=False, index=True))
    resource_name: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
        default_factory=lambda: datetime.now(timezone.utc)
    )
