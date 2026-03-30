"""
Admin router for administrative operations
"""
from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form, Query
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError
from typing import Annotated, Optional, List
from api.database import get_db
from api.dependencies.auth import require_admin
from api.services.user_service import get_all_users, grant_admin_privilege, revoke_admin_privilege, disable_user, enable_user, soft_delete_user
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
from api.services.system_setting_service import (
    get_all_system_settings,
    get_system_setting,
    set_system_setting,
    get_default_daily_token_limit,
    get_system_settings_config,
    update_system_settings_config,
)
from api.services.api_key_limit_history_service import (
    get_limit_history,
    get_all_limit_history,
)
from api.schemas.user import UserResponse, UserListResponse, RoleFilter
from api.schemas.password_reset import UserCreateRequest, PasswordResetTokenResponse
from api.services.password_reset_service import create_user_with_reset_token, reset_user_password, generate_reset_link
from api.models.user import User
from api.utils.operation_log import log_operation
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
from api.schemas.system_setting import (
    SystemSettingResponse,
    SystemSettingUpdate,
    SystemSettingsListResponse,
    SystemSettingsConfigRequest,
    SystemSettingsConfigResponse,
)
from api.schemas.operation_log import (
    OperationLogDetailList,
)
from api.services.operation_log_service import (
    get_operation_logs_with_details,
)
from api.models.operation_log import OperationType, ResourceType

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
            'is_disabled': u.is_disabled,
            'subscription_count': stats.get('subscription_count', 0),
            'active_subscription_count': stats.get('active_subscription_count', 0),
            'last_used_at': stats.get('last_used_at'),
        }
        items.append(UserWithStatsResponse(**user_dict))
    return UserListResponse(items=items, total=total)


@router.put("/users/{user_id}/grant-admin", response_model=UserResponse)
@log_operation(ResourceType.USER, OperationType.GRANT_ADMIN, resource_id_param="user_id")
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
@log_operation(ResourceType.USER, OperationType.REVOKE_ADMIN, resource_id_param="user_id")
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


@router.post("/users/create", response_model=PasswordResetTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db)
) -> PasswordResetTokenResponse:
    """
    Create a new user with force_password_change=True and generate reset token (admin only)

    Args:
        user_data: User creation data (email only)
        current_admin: Current authenticated admin user
        db: Database session

    Returns:
        Reset token and password reset link
    """
    success, reset_token, error_msg = await create_user_with_reset_token(db, user_data.email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

    # Log the operation manually since we need user_id from reset_token
    from api.services.operation_log_service import create_operation_log
    try:
        create_operation_log(
            db=db,
            user_id=current_admin.id,
            operation_type=OperationType.CREATE,
            resource_type=ResourceType.USER,
            resource_id=reset_token.user_id
        )
    except Exception as e:
        # Log failure should not affect the response
        import logging
        logging.getLogger(__name__).error(f"Failed to log operation: {e}")

    # Generate reset link using configured WEBSITE_BASE_URL
    from api.config import settings
    link = generate_reset_link(reset_token.token, settings.WEBSITE_BASE_URL)

    return PasswordResetTokenResponse(
        token=reset_token.token,
        link=link,
        expires_at=reset_token.expires_at
    )


@router.post("/users/{user_id}/reset-password", response_model=PasswordResetTokenResponse)
@log_operation(ResourceType.USER, OperationType.RESET_PASSWORD, resource_id_param="user_id")
def reset_password(
    user_id: int,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db)
) -> PasswordResetTokenResponse:
    """
    Reset user password by clearing hashed_password and generating new reset token (admin only)

    Args:
        user_id: ID of the user to reset password for
        current_admin: Current authenticated admin user
        db: Database session

    Returns:
        Reset token and password reset link
    """
    success, reset_token, error_msg = reset_user_password(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg
        )

    # Generate reset link using configured WEBSITE_BASE_URL
    from api.config import settings
    link = generate_reset_link(reset_token.token, settings.WEBSITE_BASE_URL)

    return PasswordResetTokenResponse(
        token=reset_token.token,
        link=link,
        expires_at=reset_token.expires_at
    )


@router.put("/users/{user_id}/disable", response_model=UserResponse)
@log_operation(ResourceType.USER, OperationType.DISABLE, resource_id_param="user_id")
def disable_user_endpoint(
    user_id: int,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Disable a user account (admin only)

    Args:
        user_id: ID of the user to disable
        current_admin: Current authenticated admin user
        db: Database session

    Returns:
        Updated user object
    """
    user = disable_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}/enable", response_model=UserResponse)
@log_operation(ResourceType.USER, OperationType.ENABLE, resource_id_param="user_id")
def enable_user_endpoint(
    user_id: int,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Enable a user account (admin only)

    Args:
        user_id: ID of the user to enable
        current_admin: Current authenticated admin user
        db: Database session

    Returns:
        Updated user object
    """
    user = enable_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_operation(ResourceType.USER, OperationType.DELETE, resource_id_param="user_id")
def delete_user_endpoint(
    user_id: int,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db)
) -> None:
    """
    Soft delete a user account (admin only)

    Args:
        user_id: ID of the user to delete
        current_admin: Current authenticated admin user
        db: Database session
    """
    user = soft_delete_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


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
@log_operation(ResourceType.PROVIDER, OperationType.CREATE, use_return_value=True)
async def create_provider_endpoint(
    provider_key: str = Form(...),
    name: str = Form(...),
    website: str = Form(...),
    base_url: str = Form(...),
    custom_llm_provider: str = Form("openai"),
    validation_endpoint: Optional[str] = Form(None),
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
        validation_endpoint=validation_endpoint,
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
@log_operation(ResourceType.PROVIDER, OperationType.UPDATE, resource_id_param="provider_id")
async def update_provider_endpoint(
    provider_id: int,
    name: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    base_url: Optional[str] = Form(None),
    custom_llm_provider: Optional[str] = Form(None),
    validation_endpoint: Optional[str] = Form(None),
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
        validation_endpoint=validation_endpoint,
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
@log_operation(ResourceType.PROVIDER, OperationType.DELETE, resource_id_param="provider_id")
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
@log_operation(ResourceType.PROVIDER, OperationType.ENABLE, resource_id_param="provider_id")
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
@log_operation(ResourceType.PROVIDER, OperationType.DISABLE, resource_id_param="provider_id")
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
@log_operation(ResourceType.PROVIDER_MODEL, OperationType.ENABLE, resource_id_param="model_id")
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
@log_operation(ResourceType.PROVIDER_MODEL, OperationType.DISABLE, resource_id_param="model_id")
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
@log_operation(ResourceType.PROVIDER_MODEL, OperationType.CREATE, use_return_value=True)
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
@log_operation(ResourceType.PROVIDER_MODEL, OperationType.UPDATE, resource_id_param="model_id")
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
@log_operation(ResourceType.PROVIDER_MODEL, OperationType.DELETE, resource_id_param="model_id")
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


# ==================== System Settings Routes ====================


@router.get("/system-settings", response_model=SystemSettingsListResponse)
def get_system_settings_endpoint(
    db: Session = Depends(get_db),
) -> SystemSettingsListResponse:
    """
    Get all system settings (admin only)

    Returns:
        Dictionary of all system settings
    """
    settings_dict = get_all_system_settings(db)
    return SystemSettingsListResponse(
        settings={key: SystemSettingResponse.model_validate(value)
                 for key, value in settings_dict.items()}
    )


@router.get("/system-settings/{key}", response_model=SystemSettingResponse)
def get_system_setting_endpoint(
    key: str,
    db: Session = Depends(get_db),
) -> SystemSettingResponse:
    """
    Get a single system setting by key (admin only)

    Args:
        key: Setting key
        db: Database session

    Returns:
        System setting

    Raises:
        HTTPException: If setting not found
    """
    setting = get_system_setting(db, key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )
    return SystemSettingResponse.model_validate(setting)


@router.put("/system-settings/{key}", response_model=SystemSettingResponse)
def update_system_setting_endpoint(
    key: str,
    update_data: SystemSettingUpdate,
    db: Session = Depends(get_db),
) -> SystemSettingResponse:
    """
    Update or create a system setting (admin only)

    Args:
        key: Setting key
        update_data: Update data with new value
        db: Database session

    Returns:
        Updated or created system setting
    """
    setting = set_system_setting(db, key, update_data.value)
    return SystemSettingResponse.model_validate(setting)


@router.get("/default-daily-token-limit", response_model=int)
def get_default_daily_token_limit_endpoint(
    db: Session = Depends(get_db),
) -> int:
    """
    Get the default daily token limit (admin only)

    Returns:
        Default daily token limit
    """
    return get_default_daily_token_limit(db)


@router.put("/default-daily-token-limit", response_model=SystemSettingResponse)
def update_default_daily_token_limit_endpoint(
    update_data: SystemSettingUpdate,
    db: Session = Depends(get_db),
) -> SystemSettingResponse:
    """
    Update the default daily token limit (admin only)

    Args:
        update_data: Update data with new limit value
        db: Database session

    Returns:
        Updated system setting
    """
    setting = set_system_setting(
        db,
        'default_daily_token_limit',
        update_data.value,
        description='Default daily token limit for new API keys'
    )
    return SystemSettingResponse.model_validate(setting)


@router.get("/system-settings-config", response_model=SystemSettingsConfigResponse)
def get_system_settings_config_endpoint(
    db: Session = Depends(get_db),
) -> SystemSettingsConfigResponse:
    """
    Get all system settings config (admin only)

    Returns:
        System settings config with default_daily_token_limit, max_claws_per_user, claw_apikey_daily_token_limit
    """
    config = get_system_settings_config(db)
    return SystemSettingsConfigResponse(**config)


@router.put("/system-settings-config", response_model=SystemSettingsConfigResponse)
def update_system_settings_config_endpoint(
    update_data: SystemSettingsConfigRequest,
    db: Session = Depends(get_db),
) -> SystemSettingsConfigResponse:
    """
    Update system settings config (admin only)

    Args:
        update_data: System settings config with default_daily_token_limit, max_claws_per_user, claw_apikey_daily_token_limit
        db: Database session

    Returns:
        Updated system settings config
    """
    update_system_settings_config(
        db,
        default_daily_token_limit=update_data.default_daily_token_limit,
        max_claws_per_user=update_data.max_claws_per_user,
        claw_apikey_daily_token_limit=update_data.claw_apikey_daily_token_limit
    )
    config = get_system_settings_config(db)
    return SystemSettingsConfigResponse(**config)


# ==================== API Key Limit History Routes ====================


@router.get("/api-key-limit-history")
def get_all_limit_history_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all API key limit history (admin only)

    Args:
        page: Page number
        page_size: Items per page
        db: Database session

    Returns:
        Paginated list of limit history entries
    """
    history, total = get_all_limit_history(db, page, page_size)
    return {
        "items": history,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/api-keys/{api_key_id}/limit-history")
def get_api_key_limit_history_endpoint(
    api_key_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get limit history for a specific API key (admin only)

    Args:
        api_key_id: ID of the API key
        page: Page number
        page_size: Items per page
        db: Database session

    Returns:
        Paginated list of limit history entries for the key
    """
    history, total = get_limit_history(db, api_key_id, page, page_size)
    return {
        "items": history,
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ==================== Operation Logs Routes ====================


@router.get("/operation-logs", response_model=OperationLogDetailList)
def get_operation_logs_endpoint(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: Optional[int] = Query(default=None),
    operation_type: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    start_time: Optional[str] = Query(default=None),
    end_time: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    db: Session = Depends(get_db),
) -> OperationLogDetailList:
    """
    Get operation logs with filtering and pagination (admin only)

    Args:
        offset: Number of logs to skip (for pagination)
        limit: Maximum number of logs to return
        user_id: Filter by user ID
        operation_type: Filter by operation type
        resource_type: Filter by resource type
        start_time: Filter by start time (RFC3339 format)
        end_time: Filter by end time (RFC3339 format)
        search: Search in user email, user name, and resource name
        sort_by: Field to sort by (created_at, operation_type, resource_type)
        sort_order: Sort order (asc, desc)
        db: Database session

    Returns:
        Paginated list of operation logs with user details
    """
    from datetime import datetime

    # Validate sort_by
    valid_sort_fields = ["created_at", "operation_type", "resource_type"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by: {sort_by}. Valid values: {', '.join(valid_sort_fields)}"
        )

    # Validate sort_order
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_order: {sort_order}. Valid values: asc, desc"
        )

    # Parse time filters if provided
    parsed_start_time = None
    parsed_end_time = None

    if start_time:
        try:
            parsed_start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_time format. Use RFC3339 format."
            )

    if end_time:
        try:
            parsed_end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_time format. Use RFC3339 format."
            )

    # Convert string filters to enum types (or None for "all"/empty string)
    from api.models.operation_log import OperationType, ResourceType

    op_type_enum = None
    if operation_type and operation_type != 'all' and operation_type != '':
        try:
            op_type_enum = OperationType(operation_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation_type: {operation_type}"
            )

    res_type_enum = None
    if resource_type and resource_type != 'all' and resource_type != '':
        try:
            res_type_enum = ResourceType(resource_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resource_type: {resource_type}"
            )

    return get_operation_logs_with_details(
        db=db,
        offset=offset,
        limit=limit,
        user_id=user_id,
        operation_type=op_type_enum,
        resource_type=res_type_enum,
        start_time=parsed_start_time,
        end_time=parsed_end_time,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
