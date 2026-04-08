"""
Organization schemas for request/response validation
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator, field_serializer


class OrganizationCreate(BaseModel):
    """Schema for creating a new organization"""
    name: str = Field(..., min_length=1, max_length=100, description="Organization display name")


class OrganizationResponse(BaseModel):
    """Schema for organization response"""
    id: int
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


class OrganizationMemberResponse(BaseModel):
    """Schema for organization member response"""
    id: int
    organization_id: int
    user_id: int
    role: str
    created_at: datetime


class MyOrganizationsResponse(BaseModel):
    """Schema for user's organizations response"""
    owned: list[OrganizationResponse]
    joined: list[OrganizationResponse]


class OrgMemberStats(BaseModel):
    """Single member statistics in an organization"""
    user_id: int
    email: str
    name: Optional[str] = None
    role: str
    is_disabled: bool
    org_total_tokens: int
    last_used_at: Optional[datetime] = None
    joined_at: datetime

    @field_serializer('last_used_at', 'joined_at')
    def serialize_dt(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class OrgMemberListResponse(BaseModel):
    """Response containing list of org member stats"""
    items: list[OrgMemberStats]


class OrgInviteResponse(BaseModel):
    """Response after creating an invite link"""
    token: str
    expires_at: datetime

    @field_serializer('expires_at')
    def serialize_dt(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class OrgInviteInfoResponse(BaseModel):
    """Invite link preview (no auth required)"""
    organization_name: str
    organization_slug: str
    expires_at: datetime
    is_valid: bool

    @field_serializer('expires_at')
    def serialize_dt(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


def generate_slug(name: str) -> str:
    """
    Generate a slug from organization name

    Args:
        name: Organization name

    Returns:
        URL-friendly slug string
    """
    import re
    # Convert to lowercase
    slug = name.lower()
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug
