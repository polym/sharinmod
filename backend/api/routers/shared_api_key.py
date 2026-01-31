from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from api.database import get_db
from api.models.user import User
from api.dependencies.auth import get_current_user
from api.schemas.shared_api_key import SharedAPIKeyCreate, SharedAPIKeyResponse, SharedAPIKeyList, SharedAPIKeyMetrics
from api.services.shared_api_key_service import (
    create_shared_api_key, 
    get_user_shared_api_keys,
    disable_shared_api_key,
    enable_shared_api_key,
    delete_shared_api_key,
    get_shared_api_key_metrics
)

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])


@router.post("/share", response_model=SharedAPIKeyResponse, status_code=status.HTTP_201_CREATED)
async def share_api_key(
    api_key_data: SharedAPIKeyCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Share an existing provider API key
    
    Validates API key with provider API and stores encrypted
    Each user can only share one API key per provider
    """
    result = await create_shared_api_key(
        session=session,
        user=current_user,
        provider=api_key_data.provider,
        api_key=api_key_data.api_key,
        api_key_metadata=api_key_data.api_key_metadata
    )
    
    return result["api_key"]


@router.get("/my-shared", response_model=SharedAPIKeyList)
async def get_my_shared_api_keys(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Get list of API keys I've shared
    """
    api_keys = get_user_shared_api_keys(session, current_user.id)
    
    return SharedAPIKeyList(
        total=len(api_keys),
        items=api_keys
    )


@router.put("/disable/{api_key_id}", response_model=SharedAPIKeyResponse)
async def disable_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Disable a shared API key
    
    Sets status to INACTIVE and removes model from LiteLLM
    """
    api_key = await disable_shared_api_key(session, api_key_id, current_user.id)
    return api_key


@router.put("/enable/{api_key_id}", response_model=SharedAPIKeyResponse)
async def enable_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Enable a shared API key
    
    Sets status to ACTIVE and recreates model in LiteLLM
    """
    api_key = await enable_shared_api_key(session, api_key_id, current_user.id)
    return api_key


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Delete a shared API key
    
    Removes from database and deletes model and credential from LiteLLM
    """
    await delete_shared_api_key(session, api_key_id, current_user.id)
    return None


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
