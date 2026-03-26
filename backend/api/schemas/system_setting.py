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


class SystemSettingsConfigResponse(BaseModel):
    """Response schema for system settings config"""
    default_daily_token_limit: int
    max_claws_per_user: int
    claw_apikey_daily_token_limit: Optional[int]
