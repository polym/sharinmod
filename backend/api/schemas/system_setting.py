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
