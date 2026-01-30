"""
Service layer for unified token management
"""
from sqlmodel import Session, select
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import HTTPException
import httpx

from api.models.unified_token import UnifiedToken, UnifiedTokenStatus
from api.models.user import User
from api.models.token_usage import TokenAction
from api.utils.token_generator import generate_unified_token, is_token_unique
from api.services.token_usage_service import log_token_usage
from api.config import settings


MAX_TOKENS_PER_USER = 5


async def generate_litellm_key(
    user: User,
    token_name: Optional[str] = None,
    token_ids: Optional[List[int]] = None
) -> str:
    """
    Generate a new LiteLLM API key for unified token
    
    Args:
        user: User object with litellm_user_id
        token_name: Optional name for the key
        token_ids: Optional list of shared token IDs to associate
        
    Returns:
        Generated LiteLLM API key
        
    Raises:
        HTTPException: If LiteLLM API call fails or user has no litellm_user_id
    """
    if not user.litellm_user_id:
        raise HTTPException(
            status_code=400,
            detail="User does not have a LiteLLM user ID. Please contact support."
        )
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {
            "user_id": user.litellm_user_id,
            "key_alias": token_name or f"unified_token_{datetime.utcnow().isoformat()}",
        }
        
        # Add models if token_ids provided (would need to map token_ids to model names)
        # For now, we'll allow access to all models the user has access to
        
        try:
            response = await client.post(
                f"{settings.LITELLM_BASE_URL}/key/generate",
                json=payload,
                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
            )
            response.raise_for_status()
            data = response.json()
            key = data.get("key")
            if not key:
                raise HTTPException(
                    status_code=500,
                    detail="LiteLLM API returned invalid response: missing key"
                )
            return key
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate LiteLLM key: {str(e)}"
            )


async def block_litellm_key(key: str) -> None:
    """
    Block a LiteLLM API key
    
    Args:
        key: LiteLLM API key to block
        
    Raises:
        HTTPException: If LiteLLM API call fails
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{settings.LITELLM_BASE_URL}/key/block",
                json={"key": key},
                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to block LiteLLM key: {str(e)}"
            )


async def delete_litellm_key(key: str) -> None:
    """
    Delete a LiteLLM API key
    
    Args:
        key: LiteLLM API key to delete
        
    Raises:
        HTTPException: If LiteLLM API call fails
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{settings.LITELLM_BASE_URL}/key/delete",
                json={"keys": [key]},
                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete LiteLLM key: {str(e)}"
            )


async def regenerate_litellm_key(
    user: User,
    old_key: str,
    token_name: Optional[str] = None
) -> str:
    """
    Regenerate a LiteLLM API key (delete old, create new)
    
    Args:
        user: User object with litellm_user_id
        old_key: Old LiteLLM API key to delete
        token_name: Optional name for the new key
        
    Returns:
        New generated LiteLLM API key
        
    Raises:
        HTTPException: If LiteLLM API calls fail
    """
    # Delete old key
    await delete_litellm_key(old_key)
    
    # Generate new key
    new_key = await generate_litellm_key(user, token_name)
    
    return new_key


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


async def create_unified_token_async(
    session: Session,
    user: User,
    token_name: Optional[str] = None
) -> UnifiedToken:
    """
    Generate a new unified token for user with LiteLLM integration
    
    Args:
        session: Database session
        user: Current authenticated user
        token_name: Optional user-friendly name
        
    Returns:
        Created UnifiedToken object with litellm_key
        
    Raises:
        HTTPException: If user has reached 5-token limit, token generation fails, or LiteLLM sync fails
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
    
    # Generate LiteLLM key
    try:
        litellm_key = await generate_litellm_key(user, token_name)
    except HTTPException as e:
        # LiteLLM key generation failed, abort token creation
        raise e
    
    # Create unified token record with LiteLLM key
    unified_token = UnifiedToken(
        user_id=user.id,
        token=token,
        status=UnifiedTokenStatus.ACTIVE,
        token_name=token_name,
        litellm_key=litellm_key
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


async def block_unified_token_async(
    session: Session,
    user: User,
    token_id: int
) -> None:
    """
    Block a unified token and its LiteLLM key
    
    Args:
        session: Database session
        user: Current authenticated user
        token_id: Token ID to block
        
    Raises:
        HTTPException: If token not found, not owned by user, already revoked, or LiteLLM block fails
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
    
    # Block LiteLLM key if exists
    if token.litellm_key:
        try:
            await block_litellm_key(token.litellm_key)
        except HTTPException as e:
            # Log but don't fail if LiteLLM block fails
            import logging
            logging.warning(f"Failed to block LiteLLM key: {e.detail}")
    
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
        details=f"Blocked unified token: {token.token_name or 'Unnamed'}"
    )


async def delete_unified_token_async(
    session: Session,
    user: User,
    token_id: int
) -> None:
    """
    Delete a unified token and its LiteLLM key (must be revoked first)
    
    Args:
        session: Database session
        user: Current authenticated user
        token_id: Token ID to delete
        
    Raises:
        HTTPException: If token not found, not owned by user, not revoked, or LiteLLM delete fails
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
    
    if token.status != UnifiedTokenStatus.REVOKED:
        raise HTTPException(
            status_code=400,
            detail="Token must be revoked before deletion. Use block endpoint first."
        )
    
    # Delete LiteLLM key if exists
    if token.litellm_key:
        try:
            await delete_litellm_key(token.litellm_key)
        except HTTPException as e:
            # Log but don't fail if LiteLLM delete fails
            import logging
            logging.warning(f"Failed to delete LiteLLM key: {e.detail}")
    
    # Delete token
    session.delete(token)
    session.commit()
    
    # Log deletion action
    log_token_usage(
        db=session,
        user_id=user.id,
        token_id=str(token_id),
        action=TokenAction.REVOKED,  # Reusing REVOKED as closest action
        details=f"Deleted unified token: {token.token_name or 'Unnamed'}"
    )


async def regenerate_unified_token_async(
    session: Session,
    user: User,
    token_id: int
) -> UnifiedToken:
    """
    Regenerate a unified token's LiteLLM key
    
    Args:
        session: Database session
        user: Current authenticated user
        token_id: Token ID to regenerate
        
    Returns:
        Updated UnifiedToken with new litellm_key
        
    Raises:
        HTTPException: If token not found, not owned by user, revoked, or LiteLLM regenerate fails
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
            detail="Cannot regenerate revoked token"
        )
    
    # Regenerate LiteLLM key
    old_key = token.litellm_key
    if old_key:
        try:
            new_key = await regenerate_litellm_key(user, old_key, token.token_name)
        except HTTPException as e:
            raise e
    else:
        # If no existing key, generate new one
        try:
            new_key = await generate_litellm_key(user, token.token_name)
        except HTTPException as e:
            raise e
    
    # Update token with new key
    token.litellm_key = new_key
    
    session.add(token)
    session.commit()
    session.refresh(token)
    
    # Log regeneration action
    log_token_usage(
        db=session,
        user_id=user.id,
        token_id=str(token_id),
        action=TokenAction.GENERATED,  # Reusing GENERATED as closest action
        details=f"Regenerated LiteLLM key for unified token: {token.token_name or 'Unnamed'}"
    )
    
    return token
