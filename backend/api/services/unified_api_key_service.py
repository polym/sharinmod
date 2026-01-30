"""
Service layer for unified API key management
"""
from sqlmodel import Session, select
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import HTTPException
import httpx

from api.models.unified_api_key import UnifiedAPIKey, UnifiedAPIKeyStatus
from api.models.user import User
from api.models.api_key_usage import APIKeyAction
from api.utils.token_generator import generate_unified_token, is_token_unique
from api.services.api_key_usage_service import log_api_key_usage
from api.config import settings


MAX_API_KEYS_PER_USER = 5


async def generate_litellm_key(
    user: User,
    api_key_name: Optional[str] = None,
    api_key_ids: Optional[List[int]] = None
) -> str:
    """
    Generate a new LiteLLM API key for unified API key
    
    Args:
        user: User object with litellm_user_id
        api_key_name: Optional name for the key
        api_key_ids: Optional list of shared API key IDs to associate
        
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
            "key_alias": api_key_name or f"unified_api_key_{datetime.utcnow().isoformat()}",
        }
        
        # Add models if api_key_ids provided (would need to map api_key_ids to model names)
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
    api_key_name: Optional[str] = None
) -> str:
    """
    Regenerate a LiteLLM API key (delete old, create new)
    
    Args:
        user: User object with litellm_user_id
        old_key: Old LiteLLM API key to delete
        api_key_name: Optional name for the new key
        
    Returns:
        New generated LiteLLM API key
        
    Raises:
        HTTPException: If LiteLLM API calls fail
    """
    # Delete old key
    await delete_litellm_key(old_key)
    
    # Generate new key
    new_key = await generate_litellm_key(user, api_key_name)
    
    return new_key


def count_active_user_api_keys(session: Session, user_id: int) -> int:
    """
    Count active unified API keys for a user
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        Count of ACTIVE API keys
    """
    statement = select(UnifiedAPIKey).where(
        UnifiedAPIKey.user_id == user_id,
        UnifiedAPIKey.status == UnifiedAPIKeyStatus.ACTIVE
    )
    api_keys = session.exec(statement).all()
    return len(api_keys)


async def create_unified_api_key_async(
    session: Session,
    user: User,
    api_key_name: Optional[str] = None
) -> UnifiedAPIKey:
    """
    Generate a new unified API key for user with LiteLLM integration
    
    Args:
        session: Database session
        user: Current authenticated user
        api_key_name: Optional user-friendly name
        
    Returns:
        Created UnifiedAPIKey object with litellm_key
        
    Raises:
        HTTPException: If user has reached 5-key limit, key generation fails, or LiteLLM sync fails
    """
    # Check 5-key limit
    active_count = count_active_user_api_keys(session, user.id)
    if active_count >= MAX_API_KEYS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_API_KEYS_PER_USER} API keys per user. Please revoke an existing API key first."
        )
    
    # Generate unique API key (try up to 10 times)
    max_attempts = 10
    api_key = None
    for _ in range(max_attempts):
        candidate = generate_unified_token()
        if is_token_unique(session, candidate):
            api_key = candidate
            break
    
    if api_key is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate unique API key. Please try again."
        )
    
    # Generate LiteLLM key
    try:
        litellm_key = await generate_litellm_key(user, api_key_name)
    except HTTPException as e:
        # LiteLLM key generation failed, abort API key creation
        raise e
    
    # Create unified API key record with LiteLLM key
    unified_api_key = UnifiedAPIKey(
        user_id=user.id,
        api_key=api_key,
        status=UnifiedAPIKeyStatus.ACTIVE,
        api_key_name=api_key_name,
        litellm_key=litellm_key
    )
    
    session.add(unified_api_key)
    session.commit()
    session.refresh(unified_api_key)
    
    # Log generation action
    log_api_key_usage(
        db=session,
        user_id=user.id,
        api_key_id=str(unified_api_key.id),
        action=APIKeyAction.GENERATED,
        details=f"Generated unified API key: {api_key_name or 'Unnamed'}"
    )
    
    return unified_api_key


def get_user_unified_api_keys(session: Session, user_id: int) -> List[Dict]:
    """
    Get all unified API keys for a user
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        List of dicts compatible with UnifiedAPIKeyResponse
    """
    statement = select(UnifiedAPIKey).where(
        UnifiedAPIKey.user_id == user_id
    ).order_by(UnifiedAPIKey.created_at.desc())
    
    results = session.exec(statement).all()
    return [api_key.model_dump() for api_key in results]


def revoke_unified_api_key(
    session: Session,
    user: User,
    api_key_id: int
) -> None:
    """
    Revoke a unified API key
    
    Args:
        session: Database session
        user: Current authenticated user
        api_key_id: API key ID to revoke
        
    Raises:
        HTTPException: If API key not found, not owned by user, or already revoked
    """
    statement = select(UnifiedAPIKey).where(
        UnifiedAPIKey.id == api_key_id,
        UnifiedAPIKey.user_id == user.id
    )
    
    api_key = session.exec(statement).first()
    
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found or not owned by you"
        )
    
    if api_key.status == UnifiedAPIKeyStatus.REVOKED:
        raise HTTPException(
            status_code=400,
            detail="API key already revoked"
        )
    
    # Revoke API key
    api_key.status = UnifiedAPIKeyStatus.REVOKED
    api_key.revoked_at = datetime.utcnow()
    
    session.add(api_key)
    session.commit()
    
    # Log revocation action
    log_api_key_usage(
        db=session,
        user_id=user.id,
        api_key_id=str(api_key_id),
        action=APIKeyAction.REVOKED,
        details=f"Revoked unified API key: {api_key.api_key_name or 'Unnamed'}"
    )


async def block_unified_api_key_async(
    session: Session,
    user: User,
    api_key_id: int
) -> None:
    """
    Block a unified API key and its LiteLLM key
    
    Args:
        session: Database session
        user: Current authenticated user
        api_key_id: API key ID to block
        
    Raises:
        HTTPException: If API key not found, not owned by user, already revoked, or LiteLLM block fails
    """
    statement = select(UnifiedAPIKey).where(
        UnifiedAPIKey.id == api_key_id,
        UnifiedAPIKey.user_id == user.id
    )
    
    api_key = session.exec(statement).first()
    
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found or not owned by you"
        )
    
    if api_key.status == UnifiedAPIKeyStatus.REVOKED:
        raise HTTPException(
            status_code=400,
            detail="API key already revoked"
        )
    
    # Block LiteLLM key if exists
    if api_key.litellm_key:
        try:
            await block_litellm_key(api_key.litellm_key)
        except HTTPException as e:
            # Log but don't fail if LiteLLM block fails
            import logging
            logging.warning(f"Failed to block LiteLLM key: {e.detail}")
    
    # Revoke API key
    api_key.status = UnifiedAPIKeyStatus.REVOKED
    api_key.revoked_at = datetime.utcnow()
    
    session.add(api_key)
    session.commit()
    
    # Log revocation action
    log_api_key_usage(
        db=session,
        user_id=user.id,
        api_key_id=str(api_key_id),
        action=APIKeyAction.REVOKED,
        details=f"Blocked unified API key: {api_key.api_key_name or 'Unnamed'}"
    )


async def delete_unified_api_key_async(
    session: Session,
    user: User,
    api_key_id: int
) -> None:
    """
    Delete a unified API key and its LiteLLM key (must be revoked first)
    
    Args:
        session: Database session
        user: Current authenticated user
        api_key_id: API key ID to delete
        
    Raises:
        HTTPException: If API key not found, not owned by user, not revoked, or LiteLLM delete fails
    """
    statement = select(UnifiedAPIKey).where(
        UnifiedAPIKey.id == api_key_id,
        UnifiedAPIKey.user_id == user.id
    )
    
    api_key = session.exec(statement).first()
    
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found or not owned by you"
        )
    
    if api_key.status != UnifiedAPIKeyStatus.REVOKED:
        raise HTTPException(
            status_code=400,
            detail="API key must be revoked before deletion. Use block endpoint first."
        )
    
    # Delete LiteLLM key if exists
    if api_key.litellm_key:
        try:
            await delete_litellm_key(api_key.litellm_key)
        except HTTPException as e:
            # Log but don't fail if LiteLLM delete fails
            import logging
            logging.warning(f"Failed to delete LiteLLM key: {e.detail}")
    
    # Delete API key
    session.delete(api_key)
    session.commit()
    
    # Log deletion action
    log_api_key_usage(
        db=session,
        user_id=user.id,
        api_key_id=str(api_key_id),
        action=APIKeyAction.REVOKED,  # Reusing REVOKED as closest action
        details=f"Deleted unified API key: {api_key.api_key_name or 'Unnamed'}"
    )


async def regenerate_unified_api_key_async(
    session: Session,
    user: User,
    api_key_id: int
) -> UnifiedAPIKey:
    """
    Regenerate a unified API key's LiteLLM key
    
    Args:
        session: Database session
        user: Current authenticated user
        api_key_id: API key ID to regenerate
        
    Returns:
        Updated UnifiedAPIKey with new litellm_key
        
    Raises:
        HTTPException: If API key not found, not owned by user, revoked, or LiteLLM regenerate fails
    """
    statement = select(UnifiedAPIKey).where(
        UnifiedAPIKey.id == api_key_id,
        UnifiedAPIKey.user_id == user.id
    )
    
    api_key = session.exec(statement).first()
    
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found or not owned by you"
        )
    
    if api_key.status == UnifiedAPIKeyStatus.REVOKED:
        raise HTTPException(
            status_code=400,
            detail="Cannot regenerate revoked API key"
        )
    
    # Regenerate LiteLLM key
    old_key = api_key.litellm_key
    if old_key:
        try:
            new_key = await regenerate_litellm_key(user, old_key, api_key.api_key_name)
        except HTTPException as e:
            raise e
    else:
        # If no existing key, generate new one
        try:
            new_key = await generate_litellm_key(user, api_key.api_key_name)
        except HTTPException as e:
            raise e
    
    # Update API key with new key
    api_key.litellm_key = new_key
    
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    
    # Log regeneration action
    log_api_key_usage(
        db=session,
        user_id=user.id,
        api_key_id=str(api_key_id),
        action=APIKeyAction.GENERATED,  # Reusing GENERATED as closest action
        details=f"Regenerated LiteLLM key for unified API key: {api_key.api_key_name or 'Unnamed'}"
    )
    
    return api_key
