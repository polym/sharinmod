"""
REST API endpoints for unified API key management
"""
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.schemas.unified_api_key import (
    UnifiedAPIKeyGenerate,
    UnifiedAPIKeyResponse,
    UnifiedAPIKeyList,
    UnifiedAPIKeyUpdate
)
from api.services.unified_api_key_service import (
    create_unified_api_key_async,
    get_user_unified_api_keys,
    revoke_unified_api_key,
    block_unified_api_key_async,
    unblock_unified_api_key_async,
    delete_unified_api_key_async,
    regenerate_unified_api_key_async,
    update_unified_api_key_async
)


router = APIRouter(prefix="/api/api-keys", tags=["unified-api-keys"])


@router.post("/generate", status_code=status.HTTP_201_CREATED, response_model=UnifiedAPIKeyResponse)
async def generate_api_key(
    request: UnifiedAPIKeyGenerate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Generate a new unified API key for API access
    
    - Maximum 5 active API keys per user
    - Returns 201 Created with API key details
    - Logs GENERATED action in usage history
    - Creates LiteLLM API key for the unified API key
    """
    api_key = await create_unified_api_key_async(
        session, current_user, request.api_key_name, request.description
    )
    return api_key


@router.post("/unified", status_code=status.HTTP_201_CREATED, response_model=UnifiedAPIKeyResponse)
async def create_unified_api_key_endpoint(
    request: UnifiedAPIKeyGenerate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Create a new unified API key (frontend-compatible endpoint)
    
    - Maximum 5 active API keys per user
    - Returns 201 Created with API key details
    - Creates LiteLLM API key for the unified API key
    """
    api_key = await create_unified_api_key_async(
        session, current_user, request.api_key_name, request.description
    )
    return api_key


@router.get("/my-generated", response_model=UnifiedAPIKeyList)
def get_my_generated_api_keys(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Get list of my generated unified API keys
    
    - Returns all API keys (active and revoked)
    - Ordered by creation date (newest first)
    """
    api_keys = get_user_unified_api_keys(session, current_user.id)
    return UnifiedAPIKeyList(
        total=len(api_keys),
        items=api_keys
    )


@router.get("/my-unified", response_model=UnifiedAPIKeyList)
def get_my_unified_api_keys(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Get list of my unified API keys (frontend-compatible endpoint)
    
    - Returns all API keys (active and revoked)
    - Ordered by creation date (newest first)
    """
    api_keys = get_user_unified_api_keys(session, current_user.id)
    return UnifiedAPIKeyList(
        total=len(api_keys),
        items=api_keys
    )


@router.delete("/generated/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Revoke a unified API key
    
    - Changes status to REVOKED
    - Logs REVOKED action in usage history
    - Returns 204 No Content
    """
    revoke_unified_api_key(session, current_user, api_key_id)
    return None


@router.put("/unified/{api_key_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def block_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Block a unified API key and its LiteLLM key

    - Changes status to REVOKED
    - Blocks LiteLLM key
    - Returns 204 No Content
    """
    await block_unified_api_key_async(session, current_user, api_key_id)
    return None


@router.put("/unified/{api_key_id}/unblock", status_code=status.HTTP_200_OK, response_model=UnifiedAPIKeyResponse)
async def unblock_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Unblock a unified API key and its LiteLLM key

    - Changes status from REVOKED to ACTIVE
    - Unblocks LiteLLM key
    - Returns 200 OK with updated API key
    """
    api_key = await unblock_unified_api_key_async(session, current_user, api_key_id)
    return api_key


@router.delete("/unified/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Delete a unified API key (must be revoked first)
    
    - Permanently deletes API key
    - Deletes LiteLLM key
    - Returns 204 No Content
    """
    await delete_unified_api_key_async(session, current_user, api_key_id)
    return None


@router.post("/unified/{api_key_id}/regenerate", response_model=UnifiedAPIKeyResponse)
async def regenerate_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Regenerate LiteLLM key for a unified API key
    
    - Deletes old LiteLLM key
    - Generates new LiteLLM key
    - Returns updated API key with new key
    """
    api_key = await regenerate_unified_api_key_async(session, current_user, api_key_id)
    return api_key


@router.put("/unified/{api_key_id}", response_model=UnifiedAPIKeyResponse)
async def update_api_key(
    api_key_id: int,
    request: UnifiedAPIKeyUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Update a unified API key's metadata and status
    
    - Updates name, description, and/or status
    - If status changed to REVOKED, blocks LiteLLM key
    - Returns updated API key
    """
    api_key = await update_unified_api_key_async(
        session, 
        current_user, 
        api_key_id,
        api_key_name=request.api_key_name,
        description=request.description,
        status=request.status
    )
    return api_key
