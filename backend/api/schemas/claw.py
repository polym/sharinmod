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
    qq_bot_id: str = Field(default="", max_length=255, description="QQ Bot ID (required for QQ)")
    qq_bot_secret: str = Field(default="", max_length=255, description="QQ Bot Secret (required for QQ)")
    brain_model: Optional[str] = Field(default=None, max_length=100, description="龙虾使用的模型 ID，如 'glm-4.7'")
    chat_tool: str = Field(default='QQ', max_length=50, description="对话工具 (QQ 或 FEISHU)")

    @validator('name')
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Name cannot be empty')
        if '<' in v or '>' in v or 'script' in v.lower():
            raise ValueError('Name contains potentially unsafe characters')
        return v

    @validator('qq_bot_id', 'qq_bot_secret')
    def validate_qq_bot_fields(cls, v):
        # Allow empty values for non-QQ chat tools (e.g., FEISHU)
        return v.strip()


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
    chat_tool: Optional[str] = None
    k8s_deployment_name: Optional[str]
    status: ClawStatus
    ready: Optional[bool] = Field(default=None, description="claw 容器是否 Ready (从 K8s API 实时获取)")
    created_at: datetime
    updated_at: datetime
    daily_tokens_used: int = Field(default=0, description="今日已使用 token 数量")
    daily_token_limit: Optional[int] = Field(default=None, description="每日 token 限额")
    last_reset_date: Optional[str] = Field(default=None, description="上次重置日期")

    class Config:
        from_attributes = True
        json_encoders: Dict[type[datetime], Callable] = {
            datetime: lambda v: v.isoformat() if v.tzinfo else v.replace(tzinfo=timezone.utc).isoformat()
        }


class ClawList(BaseModel):
    """List of claws with count"""
    total: int
    items: List[ClawResponse]


class ArchiveItem(BaseModel):
    """Single archive item for a claw"""
    timestamp: str = Field(description="Archive timestamp as version identifier")
    workspace_snapshot_name: Optional[str] = Field(default=None, description="Workspace VolumeSnapshot name")
    rootfs_snapshot_name: Optional[str] = Field(default=None, description="Rootfs VolumeSnapshot name")
    created_at: Optional[str] = Field(default=None, description="Archive creation time")
    ready_to_use: Optional[bool] = Field(default=None, description="Whether all snapshots in this archive are ready to use")
    auto_created: Optional[bool] = Field(default=False, description="Whether this archive was created automatically")


class ArchiveList(BaseModel):
    """List of archives for a claw"""
    total: int
    items: List[ArchiveItem]


class ArchiveCreateResponse(BaseModel):
    """Response for creating an archive"""
    timestamp: str = Field(description="Archive timestamp as version identifier")
    workspace_snapshot_name: str = Field(description="Created workspace VolumeSnapshot name")
    rootfs_snapshot_name: Optional[str] = Field(default=None, description="Created rootfs VolumeSnapshot name")
    created_at: str = Field(description="Archive creation time")
