"""Provider configuration models for dynamic provider management

This module contains the data models for storing provider and model configurations
in the database, allowing admin users to manage providers through the UI.
"""
from sqlmodel import SQLModel, Field, Index, Relationship, Column, JSON
from datetime import datetime, timezone
from typing import Optional, List


class ProviderConfig(SQLModel, table=True):
    """
    Provider configuration stored in database

    Attributes:
        id: Primary key
        provider_key: Unique identifier for the provider (e.g., 'bigmodel', 'z.ai')
        name: Display name for the provider
        website: Provider website URL
        logo_path: Path to logo image in /providers/
        is_enabled: Whether this provider is active
        created_at: When the provider config was created
        updated_at: Last update time
        models: Associated provider models (one-to-many relationship)
    """
    __tablename__ = "provider_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider_key: str = Field(unique=True, index=True, max_length=50)
    name: str = Field(max_length=200)
    website: str = Field(max_length=500)
    logo_path: Optional[str] = Field(default=None, max_length=500)
    base_url: Optional[str] = Field(default=None, max_length=500, description="API endpoint base URL (e.g. https://api.example.com/v1)")
    custom_llm_provider: str = Field(default="openai", max_length=50, description="LiteLLM provider type: openai / anthropic / openrouter")
    validation_endpoint: Optional[str] = Field(default=None, max_length=500, description="API key validation endpoint (e.g. /v1/models). Defaults to /models if empty.")
    is_enabled: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationship to models
    models: List["ProviderModel"] = Relationship(
        back_populates="provider",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ProviderModel(SQLModel, table=True):
    """
    Model configuration for a provider

    Attributes:
        id: Primary key
        provider_config_id: Foreign key to provider_configs
        model_key: Unique identifier for the model (e.g., 'glm-5')
        display_name: Human-readable model name
        description: Model description
        context_length: Maximum context window (e.g., '128k')
        max_output_length: Maximum output tokens (e.g., '4k')
        input_types: JSON array of supported input types (['Text', 'Image'])
        output_types: JSON array of supported output types (['Text'])
        coding_score: Coding benchmark score (nullable)
        is_enabled: Whether this model is active
        created_at: When the model config was created
        updated_at: Last update time
        provider: Parent provider configuration
    """
    __tablename__ = "provider_models"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider_config_id: int = Field(foreign_key="provider_configs.id", index=True)
    model_key: str = Field(max_length=100)
    real_model: Optional[str] = Field(default=None, max_length=200, description="Real model identifier for LiteLLM API calls")
    display_name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    context_length: str = Field(max_length=50)  # Store as string like '128k', '200k'
    max_output_length: str = Field(max_length=50)  # Store as string like '4k', '32k'
    input_types: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    output_types: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    coding_score: Optional[int] = Field(default=None)
    is_enabled: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Unique constraint: one model per provider
    __table_args__ = (
        Index("idx_provider_model_unique", "provider_config_id", "model_key", unique=True),
    )

    # Relationship to provider
    provider: ProviderConfig = Relationship(back_populates="models")


class GlobalModel(SQLModel, table=True):
    """
    Global model prototype stored in database

    Attributes:
        id: Primary key
        model_key: Unique model identifier (e.g., 'glm-4.7')
        display_name: Human-readable model name
        description: Model description
        context_length: Maximum context window (e.g., '128k')
        max_output_length: Maximum output tokens (e.g., '4k')
        input_types: JSON array of supported input types
        output_types: JSON array of supported output types
        coding_score: Coding benchmark score (nullable)
        created_at: When the model was created
        updated_at: Last update time
    """
    __tablename__ = "global_models"

    id: Optional[int] = Field(default=None, primary_key=True)
    model_key: str = Field(unique=True, index=True, max_length=100)
    display_name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    context_length: str = Field(max_length=50)
    max_output_length: str = Field(max_length=50)
    input_types: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    output_types: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    coding_score: Optional[int] = Field(default=None)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
