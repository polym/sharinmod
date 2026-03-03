"""
Admin router for administrative operations
"""
from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form, Query
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError
from typing import Annotated, Optional, List
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
    save_model_logo_upload,
    get_unified_model_catalog,
    list_global_models,
    create_global_model,
    update_global_model,
    delete_global_model,
    get_supported_providers_for_model,
)
from api.schemas.user import UserResponse, UserListResponse, RoleFilter
from api.schemas.provider_config import (
    ProviderConfigResponse,
    ProviderConfigCreate,
    ProviderConfigUpdate,
    ProviderModelResponse,
    ProviderModelCreate,
    ProviderModelUpdate,
    ProviderModelsUpdateRequest,
    ProviderConfigListResponse,
    ModelCatalogOverrideRequest,
    GlobalModelCreate,
    GlobalModelUpdate,
    GlobalModelResponse,
    SupportedProviderInfo,
)

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=UserListResponse)
def list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    role_filter: Optional[RoleFilter] = Query(default=None, description="Filter by role: 'all', 'admin', 'user'"),
    db: Session = Depends(get_db)
) -> UserListResponse:
    """
    Get all users with statistics (by role) - admin only

    Args:
        offset: Number of users to skip (for pagination)
        limit: Maximum number of users to return
        role_filter: Filter by role ('all', 'admin', 'user')
        db: Database session

    Returns:
        Paginated user list with total count
    """
    users, total, stats_map = get_all_users(db, offset, limit, role_filter)
    from api.schemas.user import UserWithStatsResponse
    # Build response items with user data + stats from stats_map
    items = []
    for u in users:
        stats = stats_map.get(u.id, {})
        user_dict = {
            'id': u.id,
            'email': u.email,
            'name': u.name,
            'bio': u.bio,
            'avatar_url': u.avatar_url,
            'created_at': u.created_at,
            'contributed_tokens': u.contributed_tokens,
            'consumed_tokens': u.consumed_tokens,
            'is_admin': u.is_admin,
            'subscription_count': stats.get('subscription_count', 0),
            'active_subscription_count': stats.get('active_subscription_count', 0),
            'last_used_at': stats.get('last_used_at'),
        }
        items.append(UserWithStatsResponse(**user_dict))
    return UserListResponse(items=items, total=total)


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
    base_url: str = Form(...),
    custom_llm_provider: str = Form("openai"),
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
        website=website,
        base_url=base_url,
        custom_llm_provider=custom_llm_provider,
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
    base_url: Optional[str] = Form(None),
    custom_llm_provider: Optional[str] = Form(None),
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
        base_url=base_url,
        custom_llm_provider=custom_llm_provider,
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


@router.post("/providers/{provider_id}/models", response_model=ProviderModelResponse, status_code=status.HTTP_201_CREATED)
def create_provider_model_endpoint(
    provider_id: int,
    model_data: ProviderModelCreate,
    db: Session = Depends(get_db)
) -> ProviderModelResponse:
    """
    Create a new model for a provider (admin only)

    Args:
        provider_id: Provider ID
        model_data: Model configuration data
        db: Database session

    Returns:
        Created model
    """
    # Verify provider exists
    provider = get_provider_by_id(db, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    model = create_provider_model(db, provider_id, model_data)
    return ProviderModelResponse.model_validate(model)


@router.put("/providers/models/{model_id}", response_model=ProviderModelResponse)
def update_provider_model_endpoint(
    model_id: int,
    model_data: ProviderModelUpdate,
    db: Session = Depends(get_db)
) -> ProviderModelResponse:
    """
    Update a provider model (admin only)

    Args:
        model_id: Model ID
        model_data: Model update data
        db: Database session

    Returns:
        Updated model
    """
    model = update_provider_model(db, model_id, model_data)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    return ProviderModelResponse.model_validate(model)


@router.delete("/providers/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider_model_endpoint(
    model_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a provider model (admin only)

    Args:
        model_id: Model ID
        db: Database session
    """
    success = delete_provider_model(db, model_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )


# ==================== Model Catalog Routes ====================


@router.get("/model-catalog")
def get_model_catalog(
    provider_key: Optional[str] = Query(default=None),
    enabled_only: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get merged model catalog (built-in + DB).  Admin only.

    Args:
        provider_key: Optional filter by provider key
        enabled_only: If True, only return enabled models
        db: Database session

    Returns:
        Dict with items list and total count
    """
    items = get_unified_model_catalog(db, provider_key=provider_key, enabled_only=enabled_only)
    return {"items": items, "total": len(items)}


@router.post("/model-catalog/override", response_model=ProviderModelResponse)
def override_model_config(
    data: ModelCatalogOverrideRequest,
    db: Session = Depends(get_db),
) -> ProviderModelResponse:
    """
    Create or update a DB model record for a given provider+model_key.
    Used to override built-in models or update existing DB models.
    Admin only.

    Args:
        data: Override request with provider_key, model_key, and optional fields
        db: Database session

    Returns:
        Created or updated ProviderModel
    """
    from sqlmodel import select as sql_select
    from api.models.provider_config import ProviderModel as ProviderModelDB

    provider = get_provider_by_key(db, data.provider_key)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Provider '{data.provider_key}' not found in DB. "
                "Please create the provider first via /api/admin/providers."
            ),
        )

    existing = db.exec(
        sql_select(ProviderModelDB).where(
            ProviderModelDB.provider_config_id == provider.id,
            ProviderModelDB.model_key == data.model_key,
        )
    ).first()

    if existing:
        update_data = ProviderModelUpdate(
            display_name=data.display_name,
            description=data.description,
            context_length=data.context_length,
            max_output_length=data.max_output_length,
            input_types=data.input_types,
            output_types=data.output_types,
            coding_score=data.coding_score,
            is_enabled=data.is_enabled,
        )
        model = update_provider_model(db, existing.id, update_data)
        return ProviderModelResponse.model_validate(model)
    else:
        create_data = ProviderModelCreate(
            model_key=data.model_key,
            display_name=data.display_name or data.model_key,
            description=data.description,
            context_length=data.context_length or "N/A",
            max_output_length=data.max_output_length or "N/A",
            input_types=data.input_types,
            output_types=data.output_types,
            coding_score=data.coding_score,
            is_enabled=data.is_enabled if data.is_enabled is not None else True,
        )
        model = create_provider_model(db, provider.id, create_data)
        return ProviderModelResponse.model_validate(model)


# ==================== Global Model Routes ====================

@router.get("/global-models", response_model=List[GlobalModelResponse])
def list_global_models_route(
    db: Session = Depends(get_db),
) -> List[GlobalModelResponse]:
    """列出所有全局模型，含支持的供应商信息"""
    return list_global_models(db)


@router.post("/global-models", response_model=GlobalModelResponse, status_code=201)
async def create_global_model_route(
    model_key: str = Form(...),
    display_name: str = Form(...),
    description: Optional[str] = Form(None),
    context_length: str = Form(...),
    max_output_length: str = Form(...),
    coding_score: Optional[int] = Form(None),
    input_types_json: Optional[str] = Form(None),
    output_types_json: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> GlobalModelResponse:
    """新增全局模型（multipart form，支持 logo 上传）"""
    import json as json_lib

    input_types = None
    if input_types_json:
        try:
            input_types = json_lib.loads(input_types_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid input_types_json")

    output_types = None
    if output_types_json:
        try:
            output_types = json_lib.loads(output_types_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid output_types_json")

    data = GlobalModelCreate(
        model_key=model_key,
        display_name=display_name,
        description=description,
        context_length=context_length,
        max_output_length=max_output_length,
        coding_score=coding_score,
        input_types=input_types,
        output_types=output_types,
    )

    try:
        model = create_global_model(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"model_key '{data.model_key}' 已存在")

    # Handle logo upload
    if logo and logo.filename:
        logo_url = await save_model_logo_upload(logo, model_key)
        model.logo_url = logo_url
        db.add(model)
        db.commit()
        db.refresh(model)

    providers = get_supported_providers_for_model(db, model.model_key)
    resp = GlobalModelResponse.model_validate(model)
    resp.supported_providers = [
        SupportedProviderInfo(provider_key=p.provider_key, name=p.name, logo_path=p.logo_path)
        for p in providers
    ]
    return resp


@router.put("/global-models/{model_id}", response_model=GlobalModelResponse)
async def update_global_model_route(
    model_id: int,
    display_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    context_length: Optional[str] = Form(None),
    max_output_length: Optional[str] = Form(None),
    coding_score: Optional[int] = Form(None),
    input_types_json: Optional[str] = Form(None),
    output_types_json: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> GlobalModelResponse:
    """修改全局模型（multipart form，支持 logo 上传）"""
    import json as json_lib

    update_fields: dict = {}
    if display_name is not None:
        update_fields['display_name'] = display_name
    if description is not None:
        update_fields['description'] = description
    if context_length is not None:
        update_fields['context_length'] = context_length
    if max_output_length is not None:
        update_fields['max_output_length'] = max_output_length
    if coding_score is not None:
        update_fields['coding_score'] = coding_score
    if input_types_json is not None:
        try:
            update_fields['input_types'] = json_lib.loads(input_types_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid input_types_json")
    if output_types_json is not None:
        try:
            update_fields['output_types'] = json_lib.loads(output_types_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid output_types_json")

    data = GlobalModelUpdate(**update_fields)
    model = update_global_model(db, model_id, data)

    # Handle logo upload
    if logo and logo.filename:
        logo_url = await save_model_logo_upload(logo, model.model_key)
        model.logo_url = logo_url
        db.add(model)
        db.commit()
        db.refresh(model)

    providers = get_supported_providers_for_model(db, model.model_key)
    resp = GlobalModelResponse.model_validate(model)
    resp.supported_providers = [
        SupportedProviderInfo(provider_key=p.provider_key, name=p.name, logo_path=p.logo_path)
        for p in providers
    ]
    return resp


@router.delete("/global-models/{model_id}", status_code=204)
def delete_global_model_route(
    model_id: int,
    db: Session = Depends(get_db),
) -> None:
    """删除全局模型（需先解除供应商绑定）"""
    delete_global_model(db, model_id)
