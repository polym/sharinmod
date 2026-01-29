"""
Service layer for unified token management
"""
from sqlmodel import Session, select
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import HTTPException

from api.models.unified_token import UnifiedToken, UnifiedTokenStatus
from api.models.user import User
from api.models.token_usage import TokenAction
from api.utils.token_generator import generate_unified_token, is_token_unique
from api.services.token_usage_service import log_token_usage


MAX_TOKENS_PER_USER = 5


def count_active_user_tokens(session: Session, user_id: int) -> int:
    """
    Count active unified tokens for a user
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        Count of ACTIVE tokens
    """
    statement = select(UnifiedToken).where(
        UnifiedToken.user_id == user_id,
        UnifiedToken.status == UnifiedTokenStatus.ACTIVE
    )
    tokens = session.exec(statement).all()
    return len(tokens)


def create_unified_token(
    session: Session,
    user: User,
    token_name: Optional[str] = None
) -> UnifiedToken:
    """
    Generate a new unified token for user
    
    Args:
        session: Database session
        user: Current authenticated user
        token_name: Optional user-friendly name
        
    Returns:
        Created UnifiedToken object
        
    Raises:
        HTTPException: If user has reached 5-token limit or token generation fails
    """
    # Check 5-token limit
    active_count = count_active_user_tokens(session, user.id)
    if active_count >= MAX_TOKENS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_TOKENS_PER_USER} tokens per user. Please revoke an existing token first."
        )
    
    # Generate unique token (try up to 10 times)
    max_attempts = 10
    token = None
    for _ in range(max_attempts):
        candidate = generate_unified_token()
        if is_token_unique(session, candidate):
            token = candidate
            break
    
    if token is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate unique token. Please try again."
        )
    
    # Create unified token record
    unified_token = UnifiedToken(
        user_id=user.id,
        token=token,
        status=UnifiedTokenStatus.ACTIVE,
        token_name=token_name
    )
    
    session.add(unified_token)
    session.commit()
    session.refresh(unified_token)
    
    # Log generation action
    log_token_usage(
        db=session,
        user_id=user.id,
        token_id=str(unified_token.id),
        action=TokenAction.GENERATED,
        details=f"Generated unified token: {token_name or 'Unnamed'}"
    )
    
    return unified_token


def get_user_unified_tokens(session: Session, user_id: int) -> List[Dict]:
    """
    Get all unified tokens for a user
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        List of dicts compatible with UnifiedTokenResponse
    """
    statement = select(UnifiedToken).where(
        UnifiedToken.user_id == user_id
    ).order_by(UnifiedToken.created_at.desc())
    
    results = session.exec(statement).all()
    return [token.model_dump() for token in results]


def revoke_unified_token(
    session: Session,
    user: User,
    token_id: int
) -> None:
    """
    Revoke a unified token
    
    Args:
        session: Database session
        user: Current authenticated user
        token_id: Token ID to revoke
        
    Raises:
        HTTPException: If token not found, not owned by user, or already revoked
    """
    statement = select(UnifiedToken).where(
        UnifiedToken.id == token_id,
        UnifiedToken.user_id == user.id
    )
    
    token = session.exec(statement).first()
    
    if not token:
        raise HTTPException(
            status_code=404,
            detail="Token not found or not owned by you"
        )
    
    if token.status == UnifiedTokenStatus.REVOKED:
        raise HTTPException(
            status_code=400,
            detail="Token already revoked"
        )
    
    # Revoke token
    token.status = UnifiedTokenStatus.REVOKED
    token.revoked_at = datetime.utcnow()
    
    session.add(token)
    session.commit()
    
    # Log revocation action
    log_token_usage(
        db=session,
        user_id=user.id,
        token_id=str(token_id),
        action=TokenAction.REVOKED,
        details=f"Revoked unified token: {token.token_name or 'Unnamed'}"
    )
