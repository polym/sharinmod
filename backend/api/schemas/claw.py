"""
Pydantic schemas for Claw endpoints
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime, timezone
from typing import Optional, List, Dict, Callable
from api.models.claw import ClawType, ClawStatus


class ClawCreate(BaseModel):
    """Request schema for creating a claw"""
    name: str = Field(max_length=100, description="Friendly name for the claw")
    type: ClawType = Field(description="Type of QQ bot (NanoBot, OpenClaw, ZeroBot)")
    qq_bot_id: str = Field(max_length=255, description="QQ Bot ID")
    qq_bot_secret: str = Field(max_length=255, description="QQ Bot Secret")
    brain_model: Optional[str] = Field(default=None, max_length=100, description="龙虾使用的模型 ID，如 'glm-4.7'")

    @validator('name')
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Name cannot be empty')
        if '<' in v or '>' in v or 'script' in v.lower():
            raise ValueError('Name contains potentially unsafe characters')
        return v

    @validator('qq_bot_id')
    def validate_qq_bot_id(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('QQ Bot ID cannot be empty')
        return v

    @validator('qq_bot_secret')
    def validate_qq_bot_secret(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('QQ Bot Secret cannot be empty')
        return v


class ClawUpdate(BaseModel):
    """Request schema for updating a claw name"""
    name: str = Field(max_length=100, description="Updated name for the claw")

    @validator('name')
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Name cannot be empty')
        if '<' in v or '>' in v or 'script' in v.lower():
            raise ValueError('Name contains potentially unsafe characters')
        return v


class ClawResponse(BaseModel):
    """Response schema for a claw"""
    id: int
    user_id: int
    name: str
    type: ClawType
    qq_bot_id: str
    unified_api_key_id: Optional[int]
    brain_model: Optional[str] = None
    k8s_deployment_name: Optional[str]
    status: ClawStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders: Dict[type[datetime], Callable] = {
            datetime: lambda v: v.isoformat() if v.tzinfo else v.replace(tzinfo=timezone.utc).isoformat()
        }


class ClawList(BaseModel):
    """List of claws with count"""
    total: int
    items: List[ClawResponse]
