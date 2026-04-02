"""
Pydantic schemas for system setting endpoints
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Callable


class SystemSettingResponse(BaseModel):
    """Response schema for system setting"""
    key: str
    value: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemSettingUpdate(BaseModel):
    """Request schema for updating system setting"""
    value: str = Field(..., description="New value for the setting")


class SystemSettingsListResponse(BaseModel):
    """Response schema for list of system settings"""
    settings: Dict[str, SystemSettingResponse]


class SystemSettingsConfigRequest(BaseModel):
    """Request schema for system settings config"""
    default_daily_token_limit: int = Field(..., ge=0, description="Default daily token limit for API keys")
    max_claws_per_user: int = Field(..., ge=0, description="Maximum number of claws per user")
    claw_apikey_daily_token_limit: Optional[int] = Field(None, ge=0, description="Daily token limit for claw auto-created API keys (null uses default)")
    # Backup config fields
    claws_archive_enabled: Optional[bool] = Field(None, description="Enable claw archive backup")
    claws_archive_auto_enabled: Optional[bool] = Field(None, description="Enable automatic backup")
    claws_archive_schedule_daily: Optional[str] = Field(None, description="Daily backup cron expression")
    claws_archive_schedule_interval: Optional[int] = Field(None, ge=5, le=1440, description="Interval backup minutes (5-1440)")
    claws_archive_retention_daily: Optional[int] = Field(None, ge=1, le=365, description="Daily backup retention count (1-365)")
    claws_archive_retention_interval: Optional[int] = Field(None, ge=1, le=168, description="Interval backup retention count (1-168)")
    claws_archive_max_manual: Optional[int] = Field(None, ge=1, le=100, description="Maximum manual backups (1-100)")


class SystemSettingsConfigResponse(BaseModel):
    """Response schema for system settings config"""
    default_daily_token_limit: int
    max_claws_per_user: int
    claw_apikey_daily_token_limit: Optional[int]
    # Backup config fields
    claws_archive_enabled: bool
    claws_archive_auto_enabled: bool
    claws_archive_schedule_daily: str
    claws_archive_schedule_interval: int
    claws_archive_retention_daily: int
    claws_archive_retention_interval: int
    claws_archive_max_manual: int
