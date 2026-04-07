from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import Optional
from api.database import get_db
from api.models.provider_config import ProviderModel
from api.models.user import User
from api.dependencies.auth import get_current_user
from api.schemas.shared_api_key import (
    SharedAPIKeyCreate, SharedAPIKeyUpdate, SharedAPIKeyResponse,
    SharedAPIKeyList, SharedAPIKeyMetrics
)
from api.services.shared_api_key_service import (
    create_shared_api_key,
    get_user_shared_api_keys,
    disable_shared_api_key,
    enable_shared_api_key,
    delete_shared_api_key,
    get_shared_api_key_metrics,
    update_shared_api_key
)
from api.models.operation_log import OperationType, ResourceType
from api.utils.operation_log import log_operation
from api.services.provider_config_service import get_all_providers

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])


@router.get("/providers")
async def get_providers(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Get all enabled providers for binding subscriptions

    Returns a list of enabled providers that users can bind their API keys to.
    This endpoint is accessible to all authenticated users.
    """
    from api.schemas.provider_config import ProviderConfigResponse

    providers = get_all_providers(session, skip=0, limit=100, enabled_only=True)

    return {
        "items": [
            {
                "id": p.id,
                "provider_key": p.provider_key,
                "name": p.name,
                "website": p.website,
                "logo_path": p.logo_path,
                "is_enabled": p.is_enabled,
            }
            for p in providers
        ],
        "total": len(providers)
    }


@router.post("/share", response_model=SharedAPIKeyResponse, status_code=status.HTTP_201_CREATED)
@log_operation(ResourceType.SHARED_API_KEY, OperationType.CREATE, use_return_value=True)
async def share_api_key(
    api_key_data: SharedAPIKeyCreate,
    org_id: Optional[int] = Query(None, description="组织 ID"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Share an existing provider API key

    Validates API key with provider API and stores encrypted
    Each user can only share one API key per provider per organization
    """
    result = await create_shared_api_key(
        session=session,
        user=current_user,
        provider=api_key_data.provider,
        api_key=api_key_data.api_key,
        api_key_metadata=api_key_data.api_key_metadata,
        selected_models=api_key_data.selected_models,
        organization_id=org_id
    )

    return result["api_key"]


@router.get("/my-shared", response_model=SharedAPIKeyList)
async def get_my_shared_api_keys(
    org_id: Optional[int] = Query(None, description="组织 ID"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Get list of API keys I've shared
    """
    api_keys = get_user_shared_api_keys(session, current_user.id, organization_id=org_id)

    return SharedAPIKeyList(
        total=len(api_keys),
        items=api_keys
    )


@router.put("/disable/{api_key_id}", response_model=SharedAPIKeyResponse)
@log_operation(ResourceType.SHARED_API_KEY, OperationType.DISABLE, resource_id_param="api_key_id")
async def disable_api_key(
    api_key_id: int,
    org_id: Optional[int] = Query(None, description="组织 ID"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Disable a shared API key

    Sets status to INACTIVE and removes model from LiteLLM
    """
    api_key = await disable_shared_api_key(session, api_key_id, current_user.id, organization_id=org_id)
    return api_key


@router.put("/enable/{api_key_id}", response_model=SharedAPIKeyResponse)
@log_operation(ResourceType.SHARED_API_KEY, OperationType.ENABLE, resource_id_param="api_key_id")
async def enable_api_key(
    api_key_id: int,
    org_id: Optional[int] = Query(None, description="组织 ID"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Enable a shared API key

    Sets status to ACTIVE and recreates model in LiteLLM
    """
    api_key = await enable_shared_api_key(session, api_key_id, current_user.id, organization_id=org_id)
    return api_key


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_operation(ResourceType.SHARED_API_KEY, OperationType.DELETE, resource_id_param="api_key_id")
async def delete_api_key(
    api_key_id: int,
    org_id: Optional[int] = Query(None, description="组织 ID"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Delete a shared API key

    Removes from database and deletes model and credential from LiteLLM
    """
    await delete_shared_api_key(session, api_key_id, current_user.id, organization_id=org_id)
    return None


@router.put("/shared/{api_key_id}", response_model=SharedAPIKeyResponse)
@log_operation(ResourceType.SHARED_API_KEY, OperationType.UPDATE, resource_id_param="api_key_id")
async def update_api_key(
    api_key_id: int,
    update_data: SharedAPIKeyUpdate,
    org_id: Optional[int] = Query(None, description="组织 ID"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Update a shared API key

    Supports updating API Key and/or model list
    """
    api_key, auto_removed = await update_shared_api_key(
        session=session,
        api_key_id=api_key_id,
        user_id=current_user.id,
        new_api_key=update_data.api_key,
        selected_models=update_data.selected_models,
        organization_id=org_id
    )
    response_data = api_key.model_dump()
    if auto_removed:
        response_data["warnings"] = [f"以下模型已不在当前供应商支持列表中，已自动移除: {', '.join(auto_removed)}"]
    return response_data


@router.get("/shared/{api_key_id}/metrics", response_model=SharedAPIKeyMetrics)
async def get_api_key_metrics(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Get usage metrics for a shared API key

    Returns mock data for total tokens, duration, requests, and 14-day chart
    """
    metrics = get_shared_api_key_metrics(session, api_key_id, current_user.id)
    return metrics


@router.get("/providers/{provider}/models")
async def get_provider_models(
    provider: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Get supported models for a provider from the unified model catalog.

    Returns enabled models only (from database, including those imported from YAML).
    Disabled models are excluded.
    """
    from api.services.provider_config_service import get_unified_model_catalog, get_provider_by_key

    catalog = get_unified_model_catalog(session, provider_key=provider, enabled_only=True)

    # If catalog is empty, verify the provider actually exists before returning 404
    if not catalog:
        provider_config = get_provider_by_key(session, provider)

        if not provider_config:
            raise HTTPException(
                status_code=404,
                detail=f"Provider not found: {provider}"
            )

    return {
        "provider": provider,
        "supported_models": [item["model_key"] for item in catalog],
        "models": [
            {k: v for k, v in item.items() if k != "real_model"}
            for item in catalog
        ],
    }
