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
import json


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
        # Step 1: Check if credential exists, update if exists, create if not
        credential_payload = {
            "credential_values": {
                "api_key": token,
                "api_base": api_base
            },
            "credential_info": {
                "custom_llm_provider": "OpenAI_Text"
            }
        }
        
        # Check if credential exists
        credential_check_response = await client.get(
            f"{settings.LITELLM_BASE_URL}/credentials/by_name/{credential_name}",
            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
        )
        if credential_check_response.status_code == 500:
            print(f"LiteLLM credential check failed with 500: {credential_check_response.text}")
        
        if credential_check_response.status_code == 200:
            # Credential exists, update it
            update_payload = {
                "credential_name": credential_name,
                **credential_payload
            }
            credential_response = await client.patch(
                f"{settings.LITELLM_BASE_URL}/credentials/{credential_name}",
                json=update_payload,
                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
            )
            if credential_response.status_code == 500:
                print(f"LiteLLM credential update failed with 500: {credential_response.text}")
            credential_response.raise_for_status()
        else:
            # Credential doesn't exist, create it
            create_payload = {
                "credential_name": credential_name,
                **credential_payload
            }
            credential_response = await client.post(
                f"{settings.LITELLM_BASE_URL}/credentials",
                json=create_payload,
                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
            )
            if credential_response.status_code == 500:
                print(f"LiteLLM credential creation failed with 500: {credential_response.text}")
            credential_response.raise_for_status()
        
        # Step 2: Create model in LiteLLM
        model_payload = {
            "model_name": "glm-4.7",
            "litellm_params": {
                "custom_llm_provider": "anthropic",
                "litellm_credential_name": credential_name,
                "model": "glm-4.7"
            },
            "provider": "anthropic",
            "litellm_model_name": "glm-4.7",
        }

        print("Creating model in LiteLLM with payload:", json.dumps(model_payload, indent=2))
        
        model_response = await client.post(
            f"{settings.LITELLM_BASE_URL}/model/new",
            json=model_payload,
            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
        )
        if model_response.status_code == 500:
            print(f"LiteLLM model creation failed with 500: {model_response.text}")
        model_response.raise_for_status()
        
        return model_response.json()["model_id"]


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
            model_id = await _sync_to_litellm(user, vendor, token)
            shared_token.litellm_model_id = model_id
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


async def disable_shared_token(session: Session, token_id: int, user_id: int) -> SharedToken:
    """
    Disable a shared token and remove it from LiteLLM
    
    Args:
        session: Database session
        token_id: Token ID to disable
        user_id: User ID (for authorization check)
        
    Returns:
        Updated SharedToken
        
    Raises:
        HTTPException: If token not found, not owned by user, or LiteLLM sync fails
    """
    # Get token and verify ownership
    statement = select(SharedToken).where(
        SharedToken.id == token_id,
        SharedToken.user_id == user_id
    )
    token = session.exec(statement).first()
    
    if not token:
        raise HTTPException(
            status_code=404,
            detail="Token not found or you don't have permission to modify it"
        )
    
    # Check if already inactive
    if token.status == TokenStatus.INACTIVE:
        return token
    
    # Get user info for LiteLLM sync
    user_statement = select(User).where(User.id == user_id)
    user = session.exec(user_statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store original status for rollback
    original_status = token.status
    
    # Update status to INACTIVE
    token.status = TokenStatus.INACTIVE
    token.updated_at = datetime.utcnow()
    session.add(token)
    session.commit()
    session.refresh(token)
    
    # Sync with LiteLLM - delete the model and credential (skip in testing)
    if not settings.TESTING:
        try:
            credential_name = f"{token.vendor.value}/{user.email}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Delete model from LiteLLM if model_id exists
                if token.litellm_model_id:
                    # Check if model exists before deleting
                    model_check_response = await client.get(
                        f"{settings.LITELLM_BASE_URL}/models/{token.litellm_model_id}",
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    if model_check_response.status_code == 500:
                        print(f"LiteLLM model check failed with 500: {model_check_response.text}")
                    
                    if model_check_response.status_code == 200:
                        delete_response = await client.post(
                            f"{settings.LITELLM_BASE_URL}/model/delete",
                            json={"id": token.litellm_model_id},
                            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                        )
                        if delete_response.status_code == 500:
                            print(f"LiteLLM model deletion failed with 500: {delete_response.text}")
                        delete_response.raise_for_status()
                    else:
                        # Model not found, skip deletion
                        pass
                
                # Also delete the credential to prevent accumulation
                # Check if credential exists before deleting
                credential_check_response = await client.get(
                    f"{settings.LITELLM_BASE_URL}/credentials/by_name/{credential_name}",
                    headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                )
                if credential_check_response.status_code == 500:
                    print(f"LiteLLM credential check failed with 500: {credential_check_response.text}")
                
                if credential_check_response.status_code == 200:
                    delete_credential_response = await client.delete(
                        f"{settings.LITELLM_BASE_URL}/credentials/{credential_name}",
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    if delete_credential_response.status_code == 500:
                        print(f"LiteLLM credential deletion failed with 500: {delete_credential_response.text}")
                    delete_credential_response.raise_for_status()
                else:
                    # Credential not found, skip deletion
                    pass
                
        except Exception as e:
            # Rollback status change if LiteLLM sync fails
            token.status = original_status
            token.updated_at = datetime.utcnow()
            session.add(token)
            session.commit()
            session.refresh(token)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync disable with LiteLLM: {str(e)}"
            )
    
    # Log the disable action
    # Note: Using SHARED action as TokenAction enum doesn't have DISABLED
    # TODO: Consider adding DISABLED, ENABLED, DELETED actions to TokenAction enum
    log_token_usage(
        db=session,
        user_id=user_id,
        token_id=str(token_id),
        action=TokenAction.SHARED,
        details=f"Disabled {token.vendor.value} token"
    )
    
    return token


async def enable_shared_token(session: Session, token_id: int, user_id: int) -> SharedToken:
    """
    Enable a shared token and add it back to LiteLLM
    
    Args:
        session: Database session
        token_id: Token ID to enable
        user_id: User ID (for authorization check)
        
    Returns:
        Updated SharedToken
        
    Raises:
        HTTPException: If token not found, not owned by user, or LiteLLM sync fails
    """
    # Get token and verify ownership
    statement = select(SharedToken).where(
        SharedToken.id == token_id,
        SharedToken.user_id == user_id
    )
    token = session.exec(statement).first()
    
    if not token:
        raise HTTPException(
            status_code=404,
            detail="Token not found or you don't have permission to modify it"
        )
    
    # Check if already active
    if token.status == TokenStatus.ACTIVE:
        return token
    
    # Cannot enable revoked tokens
    if token.status == TokenStatus.REVOKED:
        raise HTTPException(
            status_code=400,
            detail="Cannot enable a revoked token"
        )
    
    # Get user info for LiteLLM sync
    user_statement = select(User).where(User.id == user_id)
    user = session.exec(user_statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store original status for rollback
    original_status = token.status
    
    # Update status to ACTIVE
    token.status = TokenStatus.ACTIVE
    token.updated_at = datetime.utcnow()
    session.add(token)
    session.commit()
    session.refresh(token)
    
    # Sync with LiteLLM - recreate the model (skip in testing)
    if not settings.TESTING:
        try:
            # Decrypt token to get plain text for LiteLLM
            plain_token = decrypt_token(token.encrypted_token)
            model_id = await _sync_to_litellm(user, token.vendor, plain_token)
            token.litellm_model_id = model_id
            session.add(token)
            session.commit()
            session.refresh(token)
            
        except Exception as e:
            # Rollback status change if LiteLLM sync fails
            token.status = original_status
            token.updated_at = datetime.utcnow()
            session.add(token)
            session.commit()
            session.refresh(token)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync enable with LiteLLM: {str(e)}"
            )
    
    # Log the enable action
    # Note: Using SHARED action as TokenAction enum doesn't have ENABLED
    # TODO: Consider adding DISABLED, ENABLED, DELETED actions to TokenAction enum
    log_token_usage(
        db=session,
        user_id=user_id,
        token_id=str(token_id),
        action=TokenAction.SHARED,
        details=f"Enabled {token.vendor.value} token"
    )
    
    return token


async def delete_shared_token(session: Session, token_id: int, user_id: int) -> None:
    """
    Delete a shared token and remove it from LiteLLM
    
    This operation is idempotent for repeated deletion of the same token,
    but will return 404 if trying to delete a token that doesn't exist
    or belongs to another user (for security).
    
    Args:
        session: Database session
        token_id: Token ID to delete
        user_id: User ID (for authorization check)
        
    Raises:
        HTTPException: If token not found/not owned by user, or LiteLLM sync fails
    """
    # Get token and verify ownership
    statement = select(SharedToken).where(
        SharedToken.id == token_id,
        SharedToken.user_id == user_id
    )
    token = session.exec(statement).first()
    
    # Return 404 for non-existent or unauthorized access
    # This is important for security - don't reveal if a token_id exists
    if not token:
        raise HTTPException(
            status_code=404,
            detail="Token not found or you don't have permission to delete it"
        )
    
    # Get user info for LiteLLM sync
    user_statement = select(User).where(User.id == user_id)
    user = session.exec(user_statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Sync with LiteLLM - delete model and credential (skip in testing)
    if not settings.TESTING:
        try:
            credential_name = f"{token.vendor.value}/{user.email}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if model exists before deleting
                if token.litellm_model_id:
                    model_check_response = await client.get(
                        f"{settings.LITELLM_BASE_URL}/models/{token.litellm_model_id}",
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    if model_check_response.status_code == 500:
                        print(f"LiteLLM model check failed with 500: {model_check_response.text}")
                    
                    if model_check_response.status_code == 200:
                        # Delete model from LiteLLM
                        delete_model_response = await client.post(
                            f"{settings.LITELLM_BASE_URL}/model/delete",
                            json={"id": token.litellm_model_id},
                            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                        )
                        if delete_model_response.status_code == 500:
                            print(f"LiteLLM model deletion failed with 500: {delete_model_response.text}")
                        delete_model_response.raise_for_status()
                    else:
                        # Model not found, skip deletion
                        pass
                else:
                    # No model_id stored, skip model deletion
                    pass
                
                # Check if credential exists before deleting
                credential_check_response = await client.get(
                    f"{settings.LITELLM_BASE_URL}/credentials/by_name/{credential_name}",
                    headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                )
                if credential_check_response.status_code == 500:
                    print(f"LiteLLM credential check failed with 500: {credential_check_response.text}")
                
                if credential_check_response.status_code == 200:
                    # Delete credential from LiteLLM
                    delete_credential_response = await client.delete(
                        f"{settings.LITELLM_BASE_URL}/credentials/{credential_name}",
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    if delete_credential_response.status_code == 500:
                        print(f"LiteLLM credential deletion failed with 500: {delete_credential_response.text}")
                    delete_credential_response.raise_for_status()
                else:
                    # Credential not found, skip deletion
                    pass
                
        except Exception as e:
            # Don't delete database record if LiteLLM sync fails
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete from LiteLLM: {str(e)}"
            )
    
    # Log the delete action before deletion
    # Note: Using SHARED action as TokenAction enum doesn't have DELETED
    # TODO: Consider adding DISABLED, ENABLED, DELETED actions to TokenAction enum
    log_token_usage(
        db=session,
        user_id=user_id,
        token_id=str(token_id),
        action=TokenAction.SHARED,
        details=f"Deleted {token.vendor.value} token"
    )
    
    # Delete from database
    session.delete(token)
    session.commit()
