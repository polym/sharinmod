from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from api.database import get_db
from api.models.user import User
from api.dependencies.auth import get_current_user
from api.schemas.shared_token import SharedTokenCreate, SharedTokenResponse, SharedTokenList
from api.services.shared_token_service import (
    create_shared_token, 
    get_user_shared_tokens,
    disable_shared_token,
    enable_shared_token,
    delete_shared_token
)

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


@router.post("/share", response_model=SharedTokenResponse, status_code=status.HTTP_201_CREATED)
async def share_token(
    token_data: SharedTokenCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Share an existing vendor token
    
    Validates token with vendor API and stores encrypted
    Each user can only share one token per vendor
    """
    result = await create_shared_token(
        session=session,
        user=current_user,
        vendor=token_data.vendor,
        token=token_data.token,
        token_metadata=token_data.token_metadata
    )
    
    return result["token"]


@router.get("/my-shared", response_model=SharedTokenList)
async def get_my_shared_tokens(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Get list of tokens I've shared
    """
    tokens = get_user_shared_tokens(session, current_user.id)
    
    return SharedTokenList(
        total=len(tokens),
        items=tokens
    )


@router.put("/disable/{token_id}", response_model=SharedTokenResponse)
async def disable_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Disable a shared token
    
    Sets status to INACTIVE and removes model from LiteLLM
    """
    token = await disable_shared_token(session, token_id, current_user.id)
    return token


@router.put("/enable/{token_id}", response_model=SharedTokenResponse)
async def enable_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Enable a shared token
    
    Sets status to ACTIVE and recreates model in LiteLLM
    """
    token = await enable_shared_token(session, token_id, current_user.id)
    return token


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Delete a shared token
    
    Removes from database and deletes model and credential from LiteLLM
    """
    await delete_shared_token(session, token_id, current_user.id)
    return None
