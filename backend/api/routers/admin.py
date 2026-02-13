"""
Admin router for administrative operations
"""
from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form
from sqlmodel import Session
from typing import Annotated, Optional
from api.database import get_db
from api.dependencies.auth import require_admin
from api.services.user_service import get_all_users, grant_admin_privilege, revoke_admin_privilege
from api.services.provider_config_service import (
    get_all_providers,
    get_provider_by_id,
    get_provider_by_key,
    create_provider,
    update_provider,
    delete_provider,
    enable_provider,
    disable_provider,
    get_provider_model_by_id,
    create_provider_model,
    update_provider_model,
    delete_provider_model,
    enable_provider_model,
    disable_provider_model,
    update_provider_models_batch,
    save_logo_upload,
)
from api.schemas.user import UserResponse
from api.schemas.provider_config import (
    ProviderConfigResponse,
    ProviderConfigCreate,
    ProviderConfigUpdate,
    ProviderModelResponse,
    ProviderModelCreate,
    ProviderModelUpdate,
    ProviderModelsUpdateRequest,
    ProviderConfigListResponse,
)

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> list[UserResponse]:
    """
    Get all users (admin only)

    Args:
        offset: Number of users to skip (for pagination)
        limit: Maximum number of users to return
        db: Database session

    Returns:
        List of users
    """
    users = get_all_users(db, offset, limit)
    return [UserResponse.model_validate(u) for u in users]


@router.put("/users/{user_id}/grant-admin", response_model=UserResponse)
def grant_admin(
    user_id: int,
    current_admin: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Grant admin privileges to a user (admin only)

    Args:
        user_id: ID of the user to grant admin privileges
        current_admin: Current authenticated admin user
        db: Database session

    Returns:
        Updated user object
    """
    user = grant_admin_privilege(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}/revoke-admin", response_model=UserResponse)
def revoke_admin(
    user_id: int,
    current_admin: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Revoke admin privileges from a user (admin only)

    Args:
        user_id: ID of the user to revoke admin privileges
        current_admin: Current authenticated admin user
        db: Database session

    Returns:
        Updated user object
    """
    user = revoke_admin_privilege(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)

# ==================== Provider Configuration Routes ====================

@router.get("/providers", response_model=ProviderConfigListResponse)
def list_providers(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    db: Session = Depends(get_db)
) -> ProviderConfigListResponse:
    """
    Get all provider configurations (admin only)

    Args:
        skip: Number of providers to skip (pagination)
        limit: Maximum number of providers to return
        enabled_only: If True, only return enabled providers
        db: Database session

    Returns:
        List of provider configurations with nested models
    """
    providers = get_all_providers(db, skip, limit, enabled_only)
    return ProviderConfigListResponse(
        items=[ProviderConfigResponse.model_validate(p) for p in providers],
        total=len(providers)
    )


@router.get("/providers/{provider_id}", response_model=ProviderConfigResponse)
def get_provider(
    provider_id: int,
    db: Session = Depends(get_db)
) -> ProviderConfigResponse:
    """
    Get a single provider configuration by ID (admin only)

    Args:
        provider_id: Provider ID
        db: Database session

    Returns:
        Provider configuration with nested models
    """
    provider = get_provider_by_id(db, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    return ProviderConfigResponse.model_validate(provider)


@router.post("/providers", response_model=ProviderConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_provider_endpoint(
    provider_key: str = Form(...),
    name: str = Form(...),
    website: str = Form(...),
    logo: Optional[UploadFile] = File(None),
    models_json: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> ProviderConfigResponse:
    """
    Create a new provider configuration (admin only)

    Args:
        provider_key: Unique provider identifier
        name: Provider display name
        website: Provider website URL
        logo: Optional logo file upload
        models_json: Optional JSON string of models data
        db: Database session

    Returns:
        Created provider configuration
    """
    import json

    provider_data = ProviderConfigCreate(
        provider_key=provider_key,
        name=name,
        website=website
    )

    # Parse models from JSON if provided
    models_data = None
    if models_json:
        try:
            models_list = json.loads(models_json)
            models_data = [ProviderModelCreate(**m) for m in models_list]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid models JSON: {str(e)}"
            )

    # Handle logo upload
    logo_path = None
    if logo and logo.filename:
        logo_path = await save_logo_upload(logo, provider_key)

    # Create provider
    provider = create_provider(db, provider_data, models_data)

    # Update logo path if uploaded
    if logo_path:
        provider.logo_path = logo_path
        db.commit()
        db.refresh(provider)

    return ProviderConfigResponse.model_validate(provider)


@router.put("/providers/{provider_id}", response_model=ProviderConfigResponse)
async def update_provider_endpoint(
    provider_id: int,
    name: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    is_enabled: Optional[bool] = Form(None),
    db: Session = Depends(get_db)
) -> ProviderConfigResponse:
    """
    Update a provider configuration (admin only)

    Args:
        provider_id: Provider ID
        name: New display name
        website: New website URL
        logo: New logo file upload
        is_enabled: Enable/disable provider
        db: Database session

    Returns:
        Updated provider configuration
    """
    provider_data = ProviderConfigUpdate(
        name=name,
        website=website,
        is_enabled=is_enabled
    )

    # Handle logo upload
    new_logo_path = None
    if logo and logo.filename:
        provider = get_provider_by_id(db, provider_id)
        if provider:
            new_logo_path = await save_logo_upload(logo, provider.provider_key)

    provider = update_provider(db, provider_id, provider_data, new_logo_path)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    return ProviderConfigResponse.model_validate(provider)


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider_endpoint(
    provider_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a provider configuration (admin only)

    Args:
        provider_id: Provider ID
        db: Database session
    """
    success = delete_provider(db, provider_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )


@router.put("/providers/{provider_id}/enable", response_model=ProviderConfigResponse)
def enable_provider_endpoint(
    provider_id: int,
    db: Session = Depends(get_db)
) -> ProviderConfigResponse:
    """Enable a provider configuration (admin only)"""
    provider = enable_provider(db, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    return ProviderConfigResponse.model_validate(provider)


@router.put("/providers/{provider_id}/disable", response_model=ProviderConfigResponse)
def disable_provider_endpoint(
    provider_id: int,
    db: Session = Depends(get_db)
) -> ProviderConfigResponse:
    """Disable a provider configuration (admin only)"""
    provider = disable_provider(db, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    return ProviderConfigResponse.model_validate(provider)


@router.put("/providers/{provider_id}/models", response_model=list[ProviderModelResponse])
def update_provider_models_endpoint(
    provider_id: int,
    models_data: ProviderModelsUpdateRequest,
    db: Session = Depends(get_db)
) -> list[ProviderModelResponse]:
    """
    Batch update all models for a provider (admin only)

    Args:
        provider_id: Provider ID
        models_data: List of updated model configurations
        db: Database session

    Returns:
        Updated models
    """
    models = update_provider_models_batch(db, provider_id, models_data.models)
    return [ProviderModelResponse.model_validate(m) for m in models]


@router.put("/providers/models/{model_id}/enable", response_model=ProviderModelResponse)
def enable_provider_model_endpoint(
    model_id: int,
    db: Session = Depends(get_db)
) -> ProviderModelResponse:
    """Enable a provider model (admin only)"""
    model = enable_provider_model(db, model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    return ProviderModelResponse.model_validate(model)


@router.put("/providers/models/{model_id}/disable", response_model=ProviderModelResponse)
def disable_provider_model_endpoint(
    model_id: int,
    db: Session = Depends(get_db)
) -> ProviderModelResponse:
    """Disable a provider model (admin only)"""
    model = disable_provider_model(db, model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    return ProviderModelResponse.model_validate(model)
