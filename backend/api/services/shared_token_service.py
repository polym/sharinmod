from sqlmodel import Session, select
from api.models.shared_token import SharedToken, TokenVendor, TokenStatus
from api.models.user import User
from api.utils.encryption import encrypt_token, decrypt_token
from api.services.token_validation_service import validate_vendor_token
from api.services.token_usage_service import log_token_usage
from api.models.token_usage import TokenAction
from api.config import settings
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException
import httpx


def check_vendor_token_exists(session: Session, user_id: int, vendor: TokenVendor) -> bool:
    """
    Check if user already has a token for this vendor
    
    Args:
        session: Database session
        user_id: User ID
        vendor: Token vendor
        
    Returns:
        True if token exists for this vendor, False otherwise
    """
    statement = select(SharedToken).where(
        SharedToken.user_id == user_id,
        SharedToken.vendor == vendor
    )
    result = session.exec(statement).first()
    return result is not None


async def _sync_to_litellm(user: User, vendor: TokenVendor, token: str) -> None:
    """
    Sync shared token to LiteLLM by creating credential and model
    
    Args:
        user: User object with litellm_user_id
        vendor: Token vendor
        token: Plain text token
        
    Raises:
        Exception: If LiteLLM API calls fail
    """
    # Prepare credential and model data
    credential_name = f"{vendor.value}/{user.email}"
    api_base = settings.VENDOR_BASE_URLS.get(vendor.value)
    
    if not api_base:
        raise ValueError(f"No API base URL configured for vendor: {vendor.value}")
    
    # Verify user has LiteLLM user ID
    if not user.litellm_user_id:
        raise ValueError(f"User {user.email} does not have a LiteLLM user ID")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Step 1: Create credential in LiteLLM
        credential_payload = {
            "credential_name": credential_name,
            "credential_values": {
                "api_key": token,
                "api_base": api_base
            },
            "credential_info": {
                "vendor": vendor.value,
                "user_email": user.email
            }
        }
        
        credential_response = await client.post(
            f"{settings.LITELLM_BASE_URL}/credential",
            json=credential_payload,
            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
        )
        credential_response.raise_for_status()
        
        # Step 2: Create model in LiteLLM
        model_payload = {
            "model_name": "glm-4.7",
            "litellm_params": {
                "model": "glm-4.7",
                "api_key": f"credential:{credential_name}",
                "api_base": api_base
            },
            "model_info": {
                "id": user.litellm_user_id,
                "user_email": user.email,
                "vendor": vendor.value
            }
        }
        
        model_response = await client.post(
            f"{settings.LITELLM_BASE_URL}/model/new",
            json=model_payload,
            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
        )
        model_response.raise_for_status()


async def create_shared_token(
    session: Session,
    user: User,
    vendor: TokenVendor,
    token: str,
    token_metadata: Optional[str] = None
) -> Dict[str, any]:
    """
    Create a new shared token with validation
    
    Args:
        session: Database session
        user: Current authenticated user
        vendor: Token vendor
        token: Plain text token to share
        token_metadata: Optional metadata JSON string
        
    Returns:
        Dict with created token info and validation result
        
    Raises:
        HTTPException: If duplicate vendor or validation fails
    """
    # Check if user already has a token for this vendor
    if check_vendor_token_exists(session, user.id, vendor):
        raise HTTPException(
            status_code=400,
            detail=f"You already have a token for {vendor.value}. Each account can only add one token per vendor."
        )
    
    # Validate token with vendor API
    validation_result = await validate_vendor_token(vendor, token)
    
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=400,
            detail=f"Token validation failed: {validation_result['message']}"
        )
    
    # Encrypt token before storage
    encrypted = encrypt_token(token)
    
    # Create shared token record
    shared_token = SharedToken(
        user_id=user.id,
        vendor=vendor,
        encrypted_token=encrypted,
        status=TokenStatus.ACTIVE,
        token_metadata=token_metadata
    )
    
    session.add(shared_token)
    session.commit()
    session.refresh(shared_token)
    
    # Sync with LiteLLM (create credential and model) - skip in testing
    if not settings.TESTING:
        try:
            await _sync_to_litellm(user, vendor, token)
        except Exception as e:
            # Rollback local token creation if LiteLLM sync fails
            session.delete(shared_token)
            session.commit()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync token with LiteLLM: {str(e)}"
            )
    
    # Log sharing action in usage history
    log_token_usage(
        db=session,
        user_id=user.id,
        token_id=str(shared_token.id),
        action=TokenAction.SHARED,
        details=f"Shared {vendor.value} token"
    )
    
    return {
        "token": shared_token,
        "validation": validation_result
    }


def get_user_shared_tokens(session: Session, user_id: int) -> List[Dict]:
    """
    Get all shared tokens for a user
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        List of dicts compatible with SharedTokenResponse
    """
    statement = select(SharedToken).where(
        SharedToken.user_id == user_id
    ).order_by(SharedToken.created_at.desc())
    
    results = session.exec(statement).all()
    
    # Convert to dicts (Pydantic will handle SharedTokenResponse validation)
    return [token.model_dump() for token in results]
