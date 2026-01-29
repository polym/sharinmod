from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from api.database import get_db
from api.models.user import User
from api.dependencies.auth import get_current_user
from api.schemas.shared_token import SharedTokenCreate, SharedTokenResponse, SharedTokenList
from api.services.shared_token_service import create_shared_token, get_user_shared_tokens

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
