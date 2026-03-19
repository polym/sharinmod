"""Pydantic schemas for provider configuration API

This module contains request and response schemas for the provider config API.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


# ==================== Response Schemas ====================

class ProviderModelResponse(BaseModel):
    """Response schema for a single provider model configuration"""
    id: int
    model_key: str
    real_model: Optional[str] = None
    display_name: str
    description: Optional[str] = None
    context_length: str
    max_output_length: str
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    coding_score: Optional[int] = None
    is_enabled: bool

    model_config = {"from_attributes": True}


class ProviderModelResponsePublic(BaseModel):
    """Response schema for non-admin users (excludes real_model)"""
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
    base_url: Optional[str] = None
    custom_llm_provider: str = "openai"
    validation_endpoint: Optional[str] = None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    models: List[ProviderModelResponse] = []

    model_config = {"from_attributes": True}


# ==================== Create Schemas ====================

class ProviderModelCreate(BaseModel):
    """Schema for creating a new provider model"""
    model_key: str = Field(..., min_length=1, max_length=100)
    real_model: Optional[str] = Field(None, max_length=200)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    context_length: str = Field(..., min_length=1, max_length=50)
    max_output_length: str = Field(..., min_length=1, max_length=50)
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    coding_score: Optional[int] = Field(None, ge=0)
    is_enabled: Optional[bool] = Field(default=True)


class ProviderConfigCreate(BaseModel):
    """Schema for creating a new provider configuration"""
    provider_key: str = Field(..., min_length=1, max_length=50, pattern="^[a-z0-9.-]+$")
    name: str = Field(..., min_length=1, max_length=200)
    website: str = Field(..., min_length=1, max_length=500)
    base_url: str = Field(..., min_length=1, max_length=500, description="API endpoint base URL")
    custom_llm_provider: str = Field(default="openai", max_length=50, description="LiteLLM provider type")
    validation_endpoint: Optional[str] = Field(None, max_length=500)
    models: Optional[List[ProviderModelCreate]] = []


# ==================== Update Schemas ====================

class ProviderModelUpdate(BaseModel):
    """Schema for updating a provider model"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    real_model: Optional[str] = Field(None, max_length=200)
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
    base_url: Optional[str] = Field(None, max_length=500, description="API endpoint base URL")
    custom_llm_provider: Optional[str] = Field(None, max_length=50, description="LiteLLM provider type")
    validation_endpoint: Optional[str] = Field(None, max_length=500)
    is_enabled: Optional[bool] = None


# ==================== Batch Update Schemas ====================

class ProviderModelsUpdateRequest(BaseModel):
    """Schema for batch updating provider models"""
    models: List[ProviderModelUpdate]


class ModelCatalogOverrideRequest(BaseModel):
    """Schema for overriding (create or update) a model catalog entry"""
    provider_key: str
    model_key: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    context_length: Optional[str] = None
    max_output_length: Optional[str] = None
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    coding_score: Optional[int] = None
    is_enabled: Optional[bool] = None


# ==================== List Response ====================

class ProviderConfigListResponse(BaseModel):
    """Response schema for list of providers"""
    items: List[ProviderConfigResponse]
    total: int


# ==================== Global Model Schemas ====================

class GlobalModelCreate(BaseModel):
    """Schema for creating a new global model"""
    model_key: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    context_length: str = Field(..., min_length=1, max_length=50)
    max_output_length: str = Field(..., min_length=1, max_length=50)
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    coding_score: Optional[int] = Field(None, ge=0)


class GlobalModelUpdate(BaseModel):
    """Schema for updating a global model"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    context_length: Optional[str] = Field(None, min_length=1, max_length=50)
    max_output_length: Optional[str] = Field(None, min_length=1, max_length=50)
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    coding_score: Optional[int] = Field(None, ge=0)


class SupportedProviderInfo(BaseModel):
    """Info about a provider that supports a global model"""
    provider_key: str
    name: str
    logo_path: Optional[str] = None


class GlobalModelResponse(BaseModel):
    """Response schema for a global model with supported providers"""
    id: int
    model_key: str
    display_name: str
    description: Optional[str] = None
    context_length: str
    max_output_length: str
    input_types: Optional[List[str]] = None
    output_types: Optional[List[str]] = None
    coding_score: Optional[int] = None
    logo_url: Optional[str] = None
    supported_providers: List[SupportedProviderInfo] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
