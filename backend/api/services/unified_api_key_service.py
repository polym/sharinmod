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
from api.models.organization import Organization
from api.models.organization_member import OrganizationMember
from api.utils.token_generator import generate_unified_token, is_token_unique
from api.services.api_key_usage_service import log_api_key_usage
from api.services.system_setting_service import get_default_daily_token_limit, get_claw_apikey_daily_token_limit
from api.config import settings
from api.utils.datetime import get_today_in_timezone


MAX_API_KEYS_PER_USER = 5


def _validate_org_membership(session: Session, user_id: int, organization_id: int) -> None:
    """Raise 403 if user is not a member/owner of the given organization."""
    membership = session.exec(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == organization_id,
        )
    ).first()
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this organization"
        )


async def generate_litellm_key(
    user: User,
    api_key_name: Optional[str] = None,
    api_key_ids: Optional[List[int]] = None,
    organization_id: Optional[int] = None,
) -> Dict[str, str]:
    """
    Generate a new LiteLLM API key for unified API key

    Args:
        user: User object with litellm_user_id
        api_key_name: Optional name for the key
        api_key_ids: Optional list of shared API key IDs to associate

    Returns:
        Dict with "key" and optionally "token_id" from LiteLLM response

    Raises:
        HTTPException: If LiteLLM API call fails or user has no litellm_user_id
    """
    if not user.litellm_user_id:
        raise HTTPException(
            status_code=400,
            detail="User does not have a LiteLLM user ID. Please contact support."
        )

    if not user.email:
        raise HTTPException(
            status_code=400,
            detail="User email is required for LiteLLM key generation"
        )

    # Use lowercase email to avoid duplicates and ensure uniqueness
    # Format: {user_email}/{key_name} to avoid naming conflicts across users
    email_prefix = user.email.lower()
    async with httpx.AsyncClient(timeout=10.0) as client:
        base_alias = f"{email_prefix}/{api_key_name or f'unified_api_key_{datetime.utcnow().isoformat()}'}"
        key_alias = f"{base_alias}/org-{organization_id}" if organization_id else f"{base_alias}/public"
        payload = {
            "user_id": user.litellm_user_id,
            "key_alias": key_alias,
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
            # Return both key and token_id (if present) for tracking
            return {
                "key": key,
                "token_id": data.get("token_id", key)  # Use key as fallback if no token_id
            }
        except httpx.HTTPError as e:
            print(f"Error response: {payload} {response.text}")
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


def sync_block_litellm_key(key: str) -> None:
    """
    Synchronous version of block_litellm_key for use in non-async contexts (consumers).

    Args:
        key: LiteLLM API key to block

    Raises:
        Exception: If LiteLLM API call fails
    """
    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            f"{settings.LITELLM_BASE_URL}/key/block",
            json={"key": key},
            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
        )
        response.raise_for_status()


def sync_unlock_litellm_key(key: str) -> None:
    """
    Synchronous version of unlock_litellm_key for use in non-async contexts (consumers).

    Args:
        key: LiteLLM API key to unblock

    Raises:
        Exception: If LiteLLM API call fails
    """
    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            f"{settings.LITELLM_BASE_URL}/key/unblock",
            json={"key": key},
            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
        )
        response.raise_for_status()


async def unlock_litellm_key(key: str) -> None:
    """
    Unblock a LiteLLM API key

    Args:
        key: LiteLLM API key to unblock

    Raises:
        HTTPException: If LiteLLM API call fails
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{settings.LITELLM_BASE_URL}/key/unblock",
                json={"key": key},
                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to unlock LiteLLM key: {str(e)}"
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
    api_key_name: Optional[str] = None,
    organization_id: Optional[int] = None,
) -> Dict[str, str]:
    """
    Regenerate a LiteLLM API key (delete old, create new)

    Args:
        user: User object with litellm_user_id
        old_key: Old LiteLLM API key to delete
        api_key_name: Optional name for the new key
        organization_id: Optional organization ID for private server isolation

    Returns:
        Dict with "key" and optionally "token_id" from LiteLLM response

    Raises:
        HTTPException: If LiteLLM API calls fail
    """
    # Delete old key
    await delete_litellm_key(old_key)

    # Generate new key
    new_key = await generate_litellm_key(user, api_key_name, organization_id=organization_id)

    return new_key


def count_active_user_api_keys(session: Session, user_id: int, organization_id: Optional[int] = None) -> int:
    """
    Count active unified API keys for a user (excluding auto-created keys)

    Args:
        session: Database session
        user_id: User ID
        organization_id: If provided, count only within this org; if None, count public-area keys only.

    Returns:
        Count of ACTIVE API keys (excluding auto-created ones)
    """
    conditions = [
        UnifiedAPIKey.user_id == user_id,
        UnifiedAPIKey.status == UnifiedAPIKeyStatus.ACTIVE,
        UnifiedAPIKey.is_auto_created == False  # 只统计手动创建的
    ]
    if organization_id is not None:
        conditions.append(UnifiedAPIKey.organization_id == organization_id)
    else:
        conditions.append(UnifiedAPIKey.organization_id.is_(None))
    api_keys = session.exec(select(UnifiedAPIKey).where(*conditions)).all()
    return len(api_keys)


async def create_unified_api_key_async(
    session: Session,
    user: User,
    api_key_name: Optional[str] = None,
    description: Optional[str] = None,
    is_auto_created: bool = False,
    organization_id: Optional[int] = None,
) -> UnifiedAPIKey:
    """
    Generate a new unified API key for user with LiteLLM integration

    Args:
        session: Database session
        user: Current authenticated user
        api_key_name: Optional user-friendly name
        description: Optional description
        is_auto_created: If True, this key was auto-created for claw and doesn't count toward quota

    Returns:
        Created UnifiedAPIKey object with litellm_key

    Raises:
        HTTPException: If user has reached 5-key limit (only for manual keys), or LiteLLM sync fails
    """
    # F1: 验证 org 成员资格（仅手动创建的 Key 需要；auto_created 为系统内部调用）
    if organization_id is not None and not is_auto_created:
        _validate_org_membership(session, user.id, organization_id)

    # F4: 验证 org 是否存在，避免 LiteLLM 调用成功但 DB 插入 FK 失败导致 Key 孤儿
    if organization_id is not None:
        org = session.get(Organization, organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

    # 只有手动创建的 Key 才检查配额（F3：按 org 维度计算配额）
    if not is_auto_created:
        active_count = count_active_user_api_keys(session, user.id, organization_id=organization_id)
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
        litellm_result = await generate_litellm_key(user, api_key_name, organization_id=organization_id)
    except HTTPException as e:
        # LiteLLM key generation failed, abort API key creation
        raise e

    # Extract key and token_id from result
    litellm_key = litellm_result["key"]
    api_key_hash = litellm_result.get("token_id")

    # Get daily token limit from system settings
    # For auto-created keys (claw), use claw-specific limit if set, otherwise use default
    if is_auto_created:
        claw_limit = get_claw_apikey_daily_token_limit(session)
        daily_limit = claw_limit if claw_limit is not None else get_default_daily_token_limit(session)
    else:
        daily_limit = get_default_daily_token_limit(session)

    # Create unified API key record with LiteLLM key and hash
    unified_api_key = UnifiedAPIKey(
        user_id=user.id,
        api_key=api_key,
        status=UnifiedAPIKeyStatus.ACTIVE,
        api_key_name=api_key_name,
        description=description,
        litellm_key=litellm_key,
        api_key_hash=api_key_hash,  # Store token_id for callback matching
        is_auto_created=is_auto_created,
        organization_id=organization_id,
        daily_token_limit=daily_limit,
        daily_tokens_used=0,
        last_reset_date=get_today_in_timezone()
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


def get_user_unified_api_keys(
    session: Session,
    user_id: int,
    include_auto_created: bool = False,
    organization_id: Optional[int] = None,
    skip_org_filter: bool = False,
) -> List[Dict]:
    """
    Get all unified API keys for a user

    Args:
        session: Database session
        user_id: User ID
        include_auto_created: Whether to include auto-created keys (e.g., for claws)
        organization_id: If provided, return keys for this org only; if None, return public area keys (organization_id IS NULL)
        skip_org_filter: If True, skip org isolation entirely (for admin/background use cases)

    Returns:
        List of dicts compatible with UnifiedAPIKeyResponse
    """
    conditions = [UnifiedAPIKey.user_id == user_id]
    if not include_auto_created:
        conditions.append(UnifiedAPIKey.is_auto_created == False)
    # 组织隔离：私服传 org_id 则过滤该 org；公区则只返回 organization_id IS NULL 的
    # skip_org_filter=True 时跳过隔离，供内部/管理员调用
    if not skip_org_filter:
        if organization_id is not None:
            conditions.append(UnifiedAPIKey.organization_id == organization_id)
        else:
            conditions.append(UnifiedAPIKey.organization_id.is_(None))
    statement = select(UnifiedAPIKey).where(
        *conditions
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


async def unblock_unified_api_key_async(
    session: Session,
    user: User,
    api_key_id: int
) -> UnifiedAPIKey:
    """
    Unblock a unified API key and its LiteLLM key

    Args:
        session: Database session
        user: Current authenticated user
        api_key_id: API key ID to unblock

    Returns:
        Updated UnifiedAPIKey

    Raises:
        HTTPException: If API key not found, not owned by user, not revoked, or LiteLLM unblock fails
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

    # Check if key is disabled due to daily limit
    if api_key.status == UnifiedAPIKeyStatus.DAILY_LIMIT_EXCEEDED:
        raise HTTPException(
            status_code=400,
            detail="无法手动启用因超限被停用的 APIKey，请等待次日自动恢复"
        )

    # Only allow unblocking revoked keys
    if api_key.status != UnifiedAPIKeyStatus.REVOKED:
        raise HTTPException(
            status_code=400,
            detail="Only revoked API keys can be unblocked"
        )

    # Unblock LiteLLM key if exists
    if api_key.litellm_key:
        try:
            await unlock_litellm_key(api_key.litellm_key)
        except HTTPException as e:
            # Log but don't fail if LiteLLM unblock fails
            import logging
            logging.warning(f"Failed to unblock LiteLLM key: {e.detail}")

    # Update status to ACTIVE and clear revoked_at
    api_key.status = UnifiedAPIKeyStatus.ACTIVE
    api_key.revoked_at = None

    session.add(api_key)
    session.commit()
    session.refresh(api_key)

    # Log unblock action
    log_api_key_usage(
        db=session,
        user_id=user.id,
        api_key_id=str(api_key_id),
        action=APIKeyAction.GENERATED,  # Reusing GENERATED as closest action
        details=f"Unblocked unified API key: {api_key.api_key_name or 'Unnamed'}"
    )

    return api_key


async def delete_unified_api_key_async(
    session: Session,
    user: User,
    api_key_id: int
) -> None:
    """
    Delete a unified API key and its LiteLLM key (can be deleted in any state)

    Args:
        session: Database session
        user: Current authenticated user
        api_key_id: API key ID to delete

    Raises:
        HTTPException: If API key not found, not owned by user, or LiteLLM delete fails
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
    
    # Allow deletion in any state (ACTIVE or REVOKED)
    # Status check removed to allow direct deletion of ACTIVE keys
    
    # Delete LiteLLM key if exists
    if api_key.litellm_key:
        try:
            await delete_litellm_key(api_key.litellm_key)
        except HTTPException as e:
            # Log but don't fail if LiteLLM delete fails
            import logging
            logging.warning(f"Failed to delete LiteLLM key: {e.detail}")

    # Clear foreign key references in usage_logs before deleting
    from api.models.usage_log import UsageLog
    from sqlalchemy import update

    session.exec(
        update(UsageLog)
        .where(UsageLog.unified_api_key_id == api_key_id)
        .values(unified_api_key_id=None)  # 保留 unified_api_key_name 供历史记录查看
    )

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
            litellm_result = await regenerate_litellm_key(user, old_key, api_key.api_key_name, organization_id=api_key.organization_id)
        except HTTPException as e:
            raise e
    else:
        # If no existing key, generate new one
        try:
            litellm_result = await generate_litellm_key(user, api_key.api_key_name, organization_id=api_key.organization_id)
        except HTTPException as e:
            raise e

    # Extract key and token_id from result
    new_key = litellm_result["key"]
    new_api_key_hash = litellm_result.get("token_id")

    # Update API key with new key and hash
    api_key.litellm_key = new_key
    api_key.api_key_hash = new_api_key_hash
    
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

async def update_unified_api_key_async(
    session: Session,
    user: User,
    api_key_id: int,
    api_key_name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[UnifiedAPIKeyStatus] = None,
    daily_token_limit: Optional[int] = None
) -> UnifiedAPIKey:
    """
    Update a unified API key's metadata and status

    Args:
        session: Database session
        user: Current authenticated user
        api_key_id: API key ID to update
        api_key_name: New name (optional)
        description: New description (optional)
        status: New status (optional)
        daily_token_limit: New daily token limit (optional)

    Returns:
        Updated UnifiedAPIKey

    Raises:
        HTTPException: If API key not found or not owned by user
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

    # Check if user is trying to manually enable a key that was disabled due to daily limit
    if status == UnifiedAPIKeyStatus.ACTIVE and api_key.status == UnifiedAPIKeyStatus.DAILY_LIMIT_EXCEEDED:
        raise HTTPException(
            status_code=400,
            detail="无法手动启用因超限被停用的 APIKey，请等待次日自动恢复"
        )

    # Update fields if provided
    if api_key_name is not None:
        api_key.api_key_name = api_key_name
    
    if description is not None:
        api_key.description = description
    
    if status is not None:
        old_status = api_key.status

        # If changing to REVOKED, block LiteLLM key first before modifying state
        if status == UnifiedAPIKeyStatus.REVOKED and old_status != UnifiedAPIKeyStatus.REVOKED:
            # Block LiteLLM key if exists (do this BEFORE modifying state)
            if api_key.litellm_key:
                try:
                    await block_litellm_key(api_key.litellm_key)
                except HTTPException as e:
                    import logging
                    logging.error(f"Failed to block LiteLLM key during update: {e.detail}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to revoke API key: LiteLLM synchronization failed. {e.detail}"
                    )
            # Only modify state after LiteLLM call succeeds
            api_key.status = status
            api_key.revoked_at = datetime.utcnow()

        # If changing from REVOKED to ACTIVE, unlock the key first before modifying state
        elif status == UnifiedAPIKeyStatus.ACTIVE and old_status == UnifiedAPIKeyStatus.REVOKED:
            # Unlock LiteLLM key if exists (do this BEFORE modifying state)
            if api_key.litellm_key:
                try:
                    await unlock_litellm_key(api_key.litellm_key)
                except HTTPException as e:
                    import logging
                    logging.error(f"Failed to unlock LiteLLM key during update: {e.detail}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to activate API key: LiteLLM synchronization failed. {e.detail}"
                    )
            # Only modify state after LiteLLM call succeeds
            api_key.status = status
            api_key.revoked_at = None

        else:
            # Simple status change without LiteLLM sync
            api_key.status = status

    # Update daily_token_limit if provided
    if daily_token_limit is not None:
        # F1, F2: Validate non-negative and integer range
        if daily_token_limit < 0:
            raise HTTPException(
                status_code=400,
                detail="Daily token limit cannot be negative"
            )
        # Validate 0 value (unlimited) - only admin can set
        if daily_token_limit == 0 and not user.is_admin:
            raise HTTPException(
                status_code=400,
                detail="Only administrators can set limit to 0 (unlimited)"
            )
        # F3: Validate against system limit within transaction
        # For auto-created keys (claws), use claw-specific limit if set, otherwise use default
        if api_key.is_auto_created:
            system_limit = get_claw_apikey_daily_token_limit(session)
            if system_limit is None:
                system_limit = get_default_daily_token_limit(session)
        else:
            system_limit = get_default_daily_token_limit(session)

        if daily_token_limit > system_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Limit cannot exceed system setting of {system_limit}"
            )
        # F10: Log limit change for audit
        old_limit = api_key.daily_token_limit
        api_key.daily_token_limit = daily_token_limit
        # Note: Operation logging happens at router level via @log_operation decorator

    session.add(api_key)
    session.commit()
    session.refresh(api_key)

    return api_key
