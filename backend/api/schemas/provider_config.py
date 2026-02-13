"""Pydantic schemas for provider configuration API

This module contains request and response schemas for the provider config API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== Response Schemas ====================

class ProviderModelResponse(BaseModel):
    """Response schema for a single provider model configuration"""
    id: int
    model_key: str
    display_name: str
    description: Optional[str] = None
    context_length: str
    max_output_length: str
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    coding_score: Optional[int] = None
    is_enabled: bool

    model_config = {"from_attributes": True}


class ProviderConfigResponse(BaseModel):
    """Response schema for provider configuration with nested models"""
    id: int
    provider_key: str
    name: str
    website: str
    logo_path: Optional[str] = None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    models: List[ProviderModelResponse] = []

    model_config = {"from_attributes": True}


# ==================== Create Schemas ====================

class ProviderModelCreate(BaseModel):
    """Schema for creating a new provider model"""
    model_key: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    context_length: str = Field(..., min_length=1, max_length=50)
    max_output_length: str = Field(..., min_length=1, max_length=50)
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    coding_score: Optional[int] = Field(None, ge=0)


class ProviderConfigCreate(BaseModel):
    """Schema for creating a new provider configuration"""
    provider_key: str = Field(..., min_length=1, max_length=50, pattern="^[a-z0-9.-]+$")
    name: str = Field(..., min_length=1, max_length=200)
    website: str = Field(..., min_length=1, max_length=500)
    models: Optional[List[ProviderModelCreate]] = []


# ==================== Update Schemas ====================

class ProviderModelUpdate(BaseModel):
    """Schema for updating a provider model"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    context_length: Optional[str] = Field(None, min_length=1, max_length=50)
    max_output_length: Optional[str] = Field(None, min_length=1, max_length=50)
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    coding_score: Optional[int] = Field(None, ge=0)
    is_enabled: Optional[bool] = None


class ProviderConfigUpdate(BaseModel):
    """Schema for updating a provider configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    website: Optional[str] = Field(None, min_length=1, max_length=500)
    logo_path: Optional[str] = Field(None, max_length=500)
    is_enabled: Optional[bool] = None


# ==================== Batch Update Schemas ====================

class ProviderModelsUpdateRequest(BaseModel):
    """Schema for batch updating provider models"""
    models: List[ProviderModelUpdate]


# ==================== List Response ====================

class ProviderConfigListResponse(BaseModel):
    """Response schema for list of providers"""
    items: List[ProviderConfigResponse]
    total: int
