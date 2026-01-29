"""
Pydantic schemas for unified token API endpoints
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from api.models.unified_token import UnifiedTokenStatus


class UnifiedTokenGenerate(BaseModel):
    """Request schema for generating unified token"""
    token_name: Optional[str] = Field(None, max_length=100, description="Optional user-friendly name for the token")


class UnifiedTokenResponse(BaseModel):
    """Response schema for unified token"""
    id: int
    user_id: int
    token: str
    status: UnifiedTokenStatus
    token_name: Optional[str]
    created_at: datetime
    revoked_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UnifiedTokenList(BaseModel):
    """List of unified tokens with pagination info"""
    total: int
    items: List[UnifiedTokenResponse]
