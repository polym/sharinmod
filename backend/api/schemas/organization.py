"""
Organization schemas for request/response validation
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


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