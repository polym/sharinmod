"""Service layer for provider configuration management

This module contains business logic for provider and model CRUD operations.
"""
from sqlmodel import Session, select, and_
from sqlmodel.sql.expression import SelectOfScalar
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
import os
import aiofiles
from datetime import datetime, timezone

from api.models.provider_config import ProviderConfig, ProviderModel
from api.schemas.provider_config import (
    ProviderConfigCreate,
    ProviderConfigUpdate,
    ProviderModelCreate,
    ProviderModelUpdate,
)


# ==================== File Upload Handling ====================

PROVIDERS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '..', 'frontend', 'public', 'providers')
MAX_LOGO_SIZE = 1 * 1024 * 1024  # 1MB
ALLOWED_LOGO_TYPES = {'image/png', 'image/jpeg', 'image/jpg'}


async def save_logo_upload(file: UploadFile, provider_key: str) -> str:
    """
    Save uploaded logo file to providers directory

    Args:
        file: Uploaded file from FastAPI
        provider_key: Provider identifier for filename

    Returns:
        Relative path to saved logo file

    Raises:
        HTTPException: If file type or size is invalid
    """
    # Validate file type
    if file.content_type not in ALLOWED_LOGO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_LOGO_TYPES)}"
        )

    # Ensure providers directory exists
    os.makedirs(PROVIDERS_DIR, exist_ok=True)

    # Generate filename (use PNG extension for consistency)
    filename = f"{provider_key}-logo.png"
    filepath = os.path.join(PROVIDERS_DIR, filename)

    # Read and validate file size
    content = await file.read()
    if len(content) > MAX_LOGO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_LOGO_SIZE / 1024 / 1024}MB"
        )

    # Save file
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(content)

    # Return relative path for frontend
    return f"/providers/{filename}"


def delete_logo_file(logo_path: str) -> None:
    """
    Delete logo file from filesystem

    Args:
        logo_path: Relative path to logo file
    """
    if not logo_path:
        return

    filename = logo_path.split('/')[-1]
    filepath = os.path.join(PROVIDERS_DIR, filename)

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            # Log error but don't fail operation
            print(f"Failed to delete logo file {filepath}: {e}")


# ==================== Provider CRUD Operations ====================

def get_all_providers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False
) -> List[ProviderConfig]:
    """
    Get all provider configurations

    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        enabled_only: If True, only return enabled providers

    Returns:
        List of provider configurations with nested models
    """
    statement = select(ProviderConfig).offset(skip).limit(limit)

    if enabled_only:
        statement = statement.where(ProviderConfig.is_enabled == True)

    statement = statement.order_by(ProviderConfig.id)

    providers = db.exec(statement).all()

    # Load models for each provider
    for provider in providers:
        models_statement = select(ProviderModel).where(
            ProviderModel.provider_config_id == provider.id
        ).order_by(ProviderModel.id)
        provider.models = db.exec(models_statement).all()

    return providers


def get_provider_by_id(db: Session, provider_id: int) -> Optional[ProviderConfig]:
    """
    Get a single provider configuration by ID

    Args:
        db: Database session
        provider_id: Provider ID

    Returns:
        Provider configuration with nested models or None
    """
    provider = db.get(ProviderConfig, provider_id)

    if provider:
        models_statement = select(ProviderModel).where(
            ProviderModel.provider_config_id == provider_id
        ).order_by(ProviderModel.id)
        provider.models = db.exec(models_statement).all()

    return provider


def get_provider_by_key(db: Session, provider_key: str) -> Optional[ProviderConfig]:
    """
    Get a provider configuration by provider_key

    Args:
        db: Database session
        provider_key: Provider key (e.g., 'bigmodel')

    Returns:
        Provider configuration or None
    """
    statement = select(ProviderConfig).where(
        ProviderConfig.provider_key == provider_key
    )
    return db.exec(statement).first()


def create_provider(
    db: Session,
    provider_data: ProviderConfigCreate,
    models_data: Optional[List[ProviderModelCreate]] = None
) -> ProviderConfig:
    """
    Create a new provider configuration with optional models

    Args:
        db: Database session
        provider_data: Provider configuration data
        models_data: Optional list of model configurations

    Returns:
        Created provider configuration

    Raises:
        HTTPException: If provider_key already exists
    """
    # Check for duplicate provider_key
    existing = get_provider_by_key(db, provider_data.provider_key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider with key '{provider_data.provider_key}' already exists"
        )

    # Create provider
    provider = ProviderConfig(
        provider_key=provider_data.provider_key,
        name=provider_data.name,
        website=provider_data.website,
        is_enabled=True
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)

    # Create models if provided
    if models_data:
        for model_data in models_data:
            model = ProviderModel(
                provider_config_id=provider.id,
                model_key=model_data.model_key,
                display_name=model_data.display_name,
                description=model_data.description,
                context_length=model_data.context_length,
                max_output_length=model_data.max_output_length,
                input_types=model_data.input_types,
                output_types=model_data.output_types,
                coding_score=model_data.coding_score,
                is_enabled=True
            )
            db.add(model)
        db.commit()

    return provider


def update_provider(
    db: Session,
    provider_id: int,
    provider_data: ProviderConfigUpdate,
    new_logo_path: Optional[str] = None
) -> Optional[ProviderConfig]:
    """
    Update a provider configuration

    Args:
        db: Database session
        provider_id: Provider ID
        provider_data: Updated provider data
        new_logo_path: New logo path if uploaded

    Returns:
        Updated provider configuration or None
    """
    provider = get_provider_by_id(db, provider_id)
    if not provider:
        return None

    # Update fields
    if provider_data.name is not None:
        provider.name = provider_data.name
    if provider_data.website is not None:
        provider.website = provider_data.website
    if provider_data.is_enabled is not None:
        provider.is_enabled = provider_data.is_enabled

    # Handle logo update
    if new_logo_path is not None:
        # Delete old logo if exists
        if provider.logo_path:
            delete_logo_file(provider.logo_path)
        provider.logo_path = new_logo_path
    elif provider_data.logo_path is not None:
        # Explicitly set to None (remove logo)
        if provider.logo_path:
            delete_logo_file(provider.logo_path)
        provider.logo_path = None

    provider.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(provider)

    return provider


def delete_provider(db: Session, provider_id: int) -> bool:
    """
    Delete a provider configuration (cascades to models)

    Args:
        db: Database session
        provider_id: Provider ID

    Returns:
        True if deleted, False if not found
    """
    provider = db.get(ProviderConfig, provider_id)
    if not provider:
        return False

    # Delete logo file if exists
    if provider.logo_path:
        delete_logo_file(provider.logo_path)

    db.delete(provider)
    db.commit()
    return True


def enable_provider(db: Session, provider_id: int) -> Optional[ProviderConfig]:
    """Enable a provider configuration"""
    provider = get_provider_by_id(db, provider_id)
    if provider:
        provider.is_enabled = True
        provider.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(provider)
    return provider


def disable_provider(db: Session, provider_id: int) -> Optional[ProviderConfig]:
    """Disable a provider configuration"""
    provider = get_provider_by_id(db, provider_id)
    if provider:
        provider.is_enabled = False
        provider.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(provider)
    return provider


# ==================== Model CRUD Operations ====================

def get_all_provider_models(db: Session, provider_config_id: int) -> List[ProviderModel]:
    """Get all models for a provider"""
    statement = select(ProviderModel).where(
        ProviderModel.provider_config_id == provider_config_id
    ).order_by(ProviderModel.id)
    return db.exec(statement).all()


def get_provider_model_by_id(db: Session, model_id: int) -> Optional[ProviderModel]:
    """Get a model by ID"""
    return db.get(ProviderModel, model_id)


def create_provider_model(
    db: Session,
    provider_config_id: int,
    model_data: ProviderModelCreate
) -> ProviderModel:
    """
    Create a new model for a provider

    Args:
        db: Database session
        provider_config_id: Parent provider ID
        model_data: Model configuration data

    Returns:
        Created model

    Raises:
        HTTPException: If model_key already exists for this provider
    """
    # Check for duplicate model_key
    existing_statement = select(ProviderModel).where(
        and_(
            ProviderModel.provider_config_id == provider_config_id,
            ProviderModel.model_key == model_data.model_key
        )
    )
    existing = db.exec(existing_statement).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model with key '{model_data.model_key}' already exists for this provider"
        )

    model = ProviderModel(
        provider_config_id=provider_config_id,
        model_key=model_data.model_key,
        display_name=model_data.display_name,
        description=model_data.description,
        context_length=model_data.context_length,
        max_output_length=model_data.max_output_length,
        input_types=model_data.input_types,
        output_types=model_data.output_types,
        coding_score=model_data.coding_score,
        is_enabled=True
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def update_provider_model(
    db: Session,
    model_id: int,
    model_data: ProviderModelUpdate
) -> Optional[ProviderModel]:
    """Update a model configuration"""
    model = get_provider_model_by_id(db, model_id)
    if not model:
        return None

    if model_data.display_name is not None:
        model.display_name = model_data.display_name
    if model_data.description is not None:
        model.description = model_data.description
    if model_data.context_length is not None:
        model.context_length = model_data.context_length
    if model_data.max_output_length is not None:
        model.max_output_length = model_data.max_output_length
    if model_data.input_types is not None:
        model.input_types = model_data.input_types
    if model_data.output_types is not None:
        model.output_types = model_data.output_types
    if model_data.coding_score is not None:
        model.coding_score = model_data.coding_score
    if model_data.is_enabled is not None:
        model.is_enabled = model_data.is_enabled

    model.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(model)
    return model


def delete_provider_model(db: Session, model_id: int) -> bool:
    """Delete a model configuration"""
    model = db.get(ProviderModel, model_id)
    if not model:
        return False
    db.delete(model)
    db.commit()
    return True


def enable_provider_model(db: Session, model_id: int) -> Optional[ProviderModel]:
    """Enable a model"""
    model = get_provider_model_by_id(db, model_id)
    if model:
        model.is_enabled = True
        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(model)
    return model


def disable_provider_model(db: Session, model_id: int) -> Optional[ProviderModel]:
    """Disable a model"""
    model = get_provider_model_by_id(db, model_id)
    if model:
        model.is_enabled = False
        model.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(model)
    return model


def update_provider_models_batch(
    db: Session,
    provider_config_id: int,
    models_data: List[ProviderModelUpdate]
) -> List[ProviderModel]:
    """
    Batch update all models for a provider

    Args:
        db: Database session
        provider_config_id: Provider ID
        models_data: List of updated model data (order corresponds to model IDs)

    Returns:
        Updated models
    """
    existing_models = get_all_provider_models(db, provider_config_id)

    if len(existing_models) != len(models_data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of models does not match"
        )

    updated_models = []
    for existing, new_data in zip(existing_models, models_data):
        if new_data.display_name is not None:
            existing.display_name = new_data.display_name
        if new_data.description is not None:
            existing.description = new_data.description
        if new_data.context_length is not None:
            existing.context_length = new_data.context_length
        if new_data.max_output_length is not None:
            existing.max_output_length = new_data.max_output_length
        if new_data.input_types is not None:
            existing.input_types = new_data.input_types
        if new_data.output_types is not None:
            existing.output_types = new_data.output_types
        if new_data.coding_score is not None:
            existing.coding_score = new_data.coding_score
        if new_data.is_enabled is not None:
            existing.is_enabled = new_data.is_enabled

        existing.updated_at = datetime.now(timezone.utc)
        updated_models.append(existing)

    db.commit()
    return updated_models
