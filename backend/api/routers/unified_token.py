"""
REST API endpoints for unified token management
"""
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.schemas.unified_token import (
    UnifiedTokenGenerate,
    UnifiedTokenResponse,
    UnifiedTokenList
)
from api.services.unified_token_service import (
    create_unified_token,
    get_user_unified_tokens,
    revoke_unified_token
)


router = APIRouter(prefix="/api/tokens", tags=["unified-tokens"])


@router.post("/generate", status_code=status.HTTP_201_CREATED, response_model=UnifiedTokenResponse)
def generate_token(
    request: UnifiedTokenGenerate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Generate a new unified token for API access
    
    - Maximum 5 active tokens per user
    - Returns 201 Created with token details
    - Logs GENERATED action in usage history
    """
    token = create_unified_token(session, current_user, request.token_name)
    return token


@router.get("/my-generated", response_model=UnifiedTokenList)
def get_my_generated_tokens(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Get list of my generated unified tokens
    
    - Returns all tokens (active and revoked)
    - Ordered by creation date (newest first)
    """
    tokens = get_user_unified_tokens(session, current_user.id)
    return UnifiedTokenList(
        total=len(tokens),
        items=tokens
    )


@router.delete("/generated/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """
    Revoke a unified token
    
    - Changes status to REVOKED
    - Logs REVOKED action in usage history
    - Returns 204 No Content
    """
    revoke_unified_token(session, current_user, token_id)
    return None
