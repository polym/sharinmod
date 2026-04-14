"""Service layer for provider configuration management

This module contains business logic for provider and model CRUD operations.
"""
from sqlmodel import Session, select, and_
from sqlmodel.sql.expression import SelectOfScalar
from sqlalchemy import func
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
import os
import aiofiles
from datetime import datetime, timezone

import yaml
from api.models.provider_config import ProviderConfig, ProviderModel, GlobalModel
from api.schemas.provider_config import (
    ProviderConfigCreate,
    ProviderConfigUpdate,
    ProviderModelCreate,
    ProviderModelUpdate,
    GlobalModelCreate,
    GlobalModelUpdate,
    GlobalModelResponse,
    SupportedProviderInfo,
)
import logging

logger = logging.getLogger(__name__)


# ==================== File Upload Handling ====================

PROVIDERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'public', 'providers'))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'public', 'models'))
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


async def save_model_logo_upload(file: UploadFile, model_key: str) -> str:
    """
    Save uploaded model logo file to models directory

    Args:
        file: Uploaded file from FastAPI
        model_key: Model identifier for filename

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

    # Ensure models directory exists
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Generate filename (use PNG extension for consistency)
    filename = f"{model_key}-logo.png"
    filepath = os.path.join(MODELS_DIR, filename)

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
    return f"/models/{filename}"


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
        base_url=provider_data.base_url,
        custom_llm_provider=provider_data.custom_llm_provider,
        validation_endpoint=provider_data.validation_endpoint,
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
    if provider_data.base_url is not None:
        provider.base_url = provider_data.base_url
    if provider_data.custom_llm_provider is not None:
        provider.custom_llm_provider = provider_data.custom_llm_provider
    if provider_data.validation_endpoint is not None:
        provider.validation_endpoint = provider_data.validation_endpoint or None
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

    is_enabled_val = model_data.is_enabled if model_data.is_enabled is not None else True
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
        is_enabled=is_enabled_val
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
    if model_data.real_model is not None:
        model.real_model = model_data.real_model
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


def get_unified_model_catalog(
    db: Session,
    provider_key: Optional[str] = None,
    enabled_only: bool = False,
) -> List[dict]:
    """
    Return model catalog from database records.

    This function now only returns models from the database.
    Built-in providers are imported via import_providers_from_yaml on startup.

    Args:
        db: Database session
        provider_key: Optional filter by provider key string (e.g. "bigmodel")
        enabled_only: If True, only return models where is_enabled=True

    Returns:
        List of dicts with keys:
          db_id, provider_key, provider_name, model_key, display_name, description,
          context_length, max_output_length, input_types, output_types,
          coding_score, is_enabled, source
    """
    # Load DB models
    stmt = (
        select(ProviderModel, ProviderConfig)
        .join(ProviderConfig, ProviderModel.provider_config_id == ProviderConfig.id)
    )
    if provider_key:
        stmt = stmt.where(ProviderConfig.provider_key == provider_key)

    rows = db.exec(stmt).all()

    # Build catalog list
    catalog_list = []
    for pm, pc in rows:
        catalog_list.append({
            "db_id": pm.id,
            "provider_key": pc.provider_key,
            "provider_name": pc.name,
            "model_key": pm.model_key,
            "real_model": pm.real_model,
            "display_name": pm.display_name,
            "description": pm.description,
            "context_length": pm.context_length,
            "max_output_length": pm.max_output_length,
            "input_types": pm.input_types,
            "output_types": pm.output_types,
            "coding_score": pm.coding_score,
            "is_enabled": pm.is_enabled,
            "source": "db",
        })

    if enabled_only:
        catalog_list = [item for item in catalog_list if item["is_enabled"]]

    return catalog_list


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
        if new_data.real_model is not None:
            existing.real_model = new_data.real_model
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


# ==================== Global Model CRUD ====================

def get_supported_providers_for_model(db: Session, model_key: str) -> List[ProviderConfig]:
    """返回 DB 中 provider_models.model_key = model_key 的所有 ProviderConfig"""
    return db.exec(
        select(ProviderConfig)
        .join(ProviderModel, ProviderModel.provider_config_id == ProviderConfig.id)
        .where(ProviderModel.model_key == model_key)
        .distinct()
    ).all()


def list_global_models(db: Session) -> List[GlobalModelResponse]:
    """返回所有 GlobalModel，含 supported_providers（批量查询，无 N+1）"""
    from collections import defaultdict
    models = db.exec(select(GlobalModel).order_by(GlobalModel.created_at)).all()
    if not models:
        return []

    model_keys = [m.model_key for m in models]
    # 批量查询所有相关 ProviderModel
    provider_model_rows = db.exec(
        select(ProviderModel).where(ProviderModel.model_key.in_(model_keys))
    ).all()

    providers_by_key: dict = defaultdict(list)
    if provider_model_rows:
        provider_ids = list({pm.provider_config_id for pm in provider_model_rows})
        provider_configs = db.exec(
            select(ProviderConfig).where(ProviderConfig.id.in_(provider_ids))
        ).all()
        provider_map = {p.id: p for p in provider_configs}

        seen: set = set()
        for pm in provider_model_rows:
            pc = provider_map.get(pm.provider_config_id)
            if pc:
                dedup = (pm.model_key, pc.id)
                if dedup not in seen:
                    seen.add(dedup)
                    providers_by_key[pm.model_key].append(pc)

    result = []
    for m in models:
        resp = GlobalModelResponse.model_validate(m)
        resp.supported_providers = [
            SupportedProviderInfo(provider_key=p.provider_key, name=p.name, logo_path=p.logo_path)
            for p in providers_by_key.get(m.model_key, [])
        ]
        result.append(resp)
    return result


def create_global_model(db: Session, data: GlobalModelCreate) -> GlobalModel:
    """创建新的全局模型"""
    model = GlobalModel(**data.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def update_global_model(db: Session, model_id: int, data: GlobalModelUpdate) -> GlobalModel:
    """更新全局模型"""
    model = db.get(GlobalModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Global model not found")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(model, k, v)
    model.updated_at = datetime.now(timezone.utc)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def delete_global_model(db: Session, model_id: int) -> None:
    """删除全局模型（需先解除供应商绑定）"""
    model = db.get(GlobalModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Global model not found")
    # 检查是否有供应商绑定
    count = db.exec(
        select(func.count(ProviderModel.id))
        .where(ProviderModel.model_key == model.model_key)
    ).one()
    if count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该模型已被 {count} 个供应商使用，请先在供应商模型中删除对应记录"
        )
    db.delete(model)
    db.commit()


# ==================== Startup Sync ====================

def import_providers_from_yaml(db: Session, yaml_path: str) -> dict:
    """Import providers and models from a YAML configuration file.

    This function performs an upsert operation:
    - If a provider_key exists in DB, update it (preserve logo_path)
    - If a provider_key doesn't exist, create it
    - For models, also perform upsert (provider_key + model_key as unique key)

    Args:
        db: Database session
        yaml_path: Path to the YAML configuration file

    Returns:
        Dictionary with statistics:
        {
            "providers_created": int,
            "providers_updated": int,
            "models_created": int,
            "models_updated": int
        }
    """
    stats = {
        "providers_created": 0,
        "providers_updated": 0,
        "models_created": 0,
        "models_updated": 0
    }

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Provider YAML file not found: {yaml_path}")
        return stats
    except Exception as e:
        logger.error(f"Failed to parse provider YAML file {yaml_path}: {e}")
        return stats

    if not yaml_data or "providers" not in yaml_data:
        logger.warning(f"Invalid YAML: 'providers' section not found")
        return stats

    for provider_data in yaml_data["providers"]:
        provider_key = provider_data.get("provider_key")
        if not provider_key:
            logger.warning("Provider entry missing 'provider_key', skipping")
            continue

        # Check if provider exists
        existing_provider = get_provider_by_key(db, provider_key)

        if existing_provider:
            # Update existing provider (preserve logo_path)
            existing_provider.name = provider_data.get("name", existing_provider.name)
            existing_provider.website = provider_data.get("website", existing_provider.website)
            existing_provider.base_url = provider_data.get("base_url", existing_provider.base_url)
            existing_provider.custom_llm_provider = provider_data.get("custom_llm_provider", existing_provider.custom_llm_provider)
            existing_provider.validation_endpoint = provider_data.get("validation_endpoint", existing_provider.validation_endpoint)
            # logo_path is explicitly preserved, not updated
            existing_provider.updated_at = datetime.now(timezone.utc)

            stats["providers_updated"] += 1
            provider = existing_provider
        else:
            # Create new provider
            logo_path = provider_data.get("logo_path")
            if not logo_path:  # Handle None and empty string
                logo_path = f"/providers/{provider_key}-logo.png"

            provider = ProviderConfig(
                provider_key=provider_key,
                name=provider_data.get("name", provider_key),
                website=provider_data.get("website"),
                base_url=provider_data.get("base_url"),
                custom_llm_provider=provider_data.get("custom_llm_provider"),
                validation_endpoint=provider_data.get("validation_endpoint"),
                logo_path=logo_path,
                is_enabled=True
            )
            db.add(provider)
            db.flush()  # Get the ID
            stats["providers_created"] += 1

        # Handle models
        models_data = provider_data.get("models", [])
        for model_data in models_data:
            model_key = model_data.get("model_key")
            if not model_key:
                continue

            # Check if model exists for this provider
            existing_model = db.exec(
                select(ProviderModel).where(
                    and_(
                        ProviderModel.provider_config_id == provider.id,
                        ProviderModel.model_key == model_key
                    )
                )
            ).first()

            if existing_model:
                # Update existing model
                if "display_name" in model_data:
                    existing_model.display_name = model_data["display_name"]
                if "description" in model_data:
                    existing_model.description = model_data["description"]
                if "context_length" in model_data:
                    existing_model.context_length = model_data["context_length"]
                if "max_output_length" in model_data:
                    existing_model.max_output_length = model_data["max_output_length"]
                if "input_types" in model_data:
                    existing_model.input_types = model_data["input_types"]
                if "output_types" in model_data:
                    existing_model.output_types = model_data["output_types"]
                if "coding_score" in model_data:
                    existing_model.coding_score = model_data["coding_score"]
                existing_model.updated_at = datetime.now(timezone.utc)

                stats["models_updated"] += 1
            else:
                # Create new model
                new_model = ProviderModel(
                    provider_config_id=provider.id,
                    model_key=model_key,
                    display_name=model_data.get("display_name", model_key),
                    description=model_data.get("description"),
                    context_length=model_data.get("context_length"),
                    max_output_length=model_data.get("max_output_length"),
                    input_types=model_data.get("input_types"),
                    output_types=model_data.get("output_types"),
                    coding_score=model_data.get("coding_score"),
                    is_enabled=True
                )
                db.add(new_model)
                stats["models_created"] += 1

        db.commit()
        db.refresh(provider)

    logger.info(
        f"✓ Imported providers from YAML: "
        f"{stats['providers_created']} created, {stats['providers_updated']} updated, "
        f"{stats['models_created']} models created, {stats['models_updated']} models updated"
    )

    return stats


def sync_global_models_from_catalog(db: Session) -> int:
    """从数据库同步全局模型到 global_models 表（已废弃）。

    此函数已废弃。请使用 import_providers_from_yaml 代替。
    保留此函数仅为向后兼容，现在直接返回 0。

    Returns:
        0 (不再执行任何操作)

    Deprecated: This function is deprecated. Use import_providers_from_yaml instead.
    """
    logger.warning("sync_global_models_from_catalog is deprecated and no longer performs any action. "
                   "Use import_providers_from_yaml to import providers from etc/providers.yaml")
    return 0
