from sqlmodel import Session, select
from api.models.shared_api_key import SharedAPIKey, APIKeyProvider, APIKeyStatus
from api.models.user import User
from api.utils.encryption import encrypt_token, decrypt_token
from api.services.api_key_validation_service import validate_api_key
from api.services.api_key_usage_service import log_api_key_usage
from api.models.api_key_usage import APIKeyAction
from api.config import settings
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from fastapi import HTTPException
import httpx
import json
import random


# Provider configuration for supported models, websites, and logo paths
PROVIDER_INFO = {
    APIKeyProvider.BIGMODEL: {
        "name": "智谱 AI Coding Plan",
        "website": "https://bigmodel.cn",
        "supported_models": ["glm-4.7", "glm-4.6", "glm-4.5-air"],
        "logo_path": "/providers/bigmodel-logo.png"
    },
    APIKeyProvider.ZAI: {
        "name": "Z.AI Coding Plan",
        "website": "https://z.ai",
        "supported_models": ["glm-4.7", "glm-4.6", "glm-4.5-air"],
        "logo_path": "/providers/zai-logo.png"
    }
}


def check_provider_api_key_exists(session: Session, user_id: int, provider: APIKeyProvider) -> bool:
    """
    Check if user already has an API key for this provider
    
    Args:
        session: Database session
        user_id: User ID
        provider: API key provider
        
    Returns:
        True if API key exists for this provider, False otherwise
    """
    statement = select(SharedAPIKey).where(
        SharedAPIKey.user_id == user_id,
        SharedAPIKey.provider == provider
    )
    result = session.exec(statement).first()
    return result is not None


async def _sync_to_litellm(user: User, provider: APIKeyProvider, api_key: str) -> None:
    """
    Sync shared API key to LiteLLM by creating credential and model
    
    Args:
        user: User object with litellm_user_id
        provider: API key provider
        api_key: Plain text API key
        
    Raises:
        Exception: If LiteLLM API calls fail
    """
    # Prepare credential and model data
    credential_name = f"{provider.value}/{user.email}"
    api_base = settings.VENDOR_BASE_URLS.get(provider.value)
    
    if not api_base:
        raise ValueError(f"No API base URL configured for provider: {provider.value}")
    
    # Verify user has LiteLLM user ID
    if not user.litellm_user_id:
        raise ValueError(f"User {user.email} does not have a LiteLLM user ID")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Step 1: Check if credential exists, update if exists, create if not
        credential_payload = {
            "credential_values": {
                "api_key": api_key,
                "api_base": api_base
            },
            "credential_info": {
                "custom_llm_provider": "anthropic"
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


async def create_shared_api_key(
    session: Session,
    user: User,
    provider: APIKeyProvider,
    api_key: str,
    api_key_metadata: Optional[str] = None
) -> Dict[str, any]:
    """
    Create a new shared API key with validation
    
    Args:
        session: Database session
        user: Current authenticated user
        provider: API key provider
        api_key: Plain text API key to share
        api_key_metadata: Optional metadata JSON string
        
    Returns:
        Dict with created API key info and validation result
        
    Raises:
        HTTPException: If duplicate provider or validation fails
    """
    # Check if user already has an API key for this provider
    if check_provider_api_key_exists(session, user.id, provider):
        raise HTTPException(
            status_code=400,
            detail=f"You already have an API key for {provider.value}. Each account can only add one API key per provider."
        )
    
    # Validate API key with provider API
    validation_result = await validate_api_key(provider, api_key)
    
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=400,
            detail=f"API key validation failed: {validation_result['message']}"
        )
    
    # Encrypt API key before storage
    encrypted = encrypt_token(api_key)
    
    # Create shared API key record
    shared_api_key = SharedAPIKey(
        user_id=user.id,
        provider=provider,
        encrypted_api_key=encrypted,
        status=APIKeyStatus.ACTIVE,
        api_key_metadata=api_key_metadata
    )
    
    session.add(shared_api_key)
    session.commit()
    session.refresh(shared_api_key)
    
    # Sync with LiteLLM (create credential and model) - skip in testing
    if not settings.TESTING:
        try:
            model_id = await _sync_to_litellm(user, provider, api_key)
            shared_api_key.litellm_model_id = model_id
        except Exception as e:
            # Rollback local API key creation if LiteLLM sync fails
            session.delete(shared_api_key)
            session.commit()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync API key with LiteLLM: {str(e)}"
            )
    
    # Log sharing action in usage history
    log_api_key_usage(
        db=session,
        user_id=user.id,
        api_key_id=str(shared_api_key.id),
        action=APIKeyAction.SHARED,
        details=f"Shared {provider.value} API key"
    )
    
    return {
        "api_key": shared_api_key,
        "validation": validation_result
    }


def get_user_shared_api_keys(session: Session, user_id: int) -> List[Dict]:
    """
    Get all shared API keys for a user with provider info
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        List of dicts compatible with SharedAPIKeyResponse (with provider info)
    """
    statement = select(SharedAPIKey).where(
        SharedAPIKey.user_id == user_id
    ).order_by(SharedAPIKey.created_at.desc())
    
    results = session.exec(statement).all()
    
    # Convert to dicts and add provider info
    api_keys = []
    for api_key in results:
        api_key_dict = api_key.model_dump()
        provider_info = PROVIDER_INFO.get(api_key.provider, {})
        api_key_dict['supported_models'] = provider_info.get('supported_models')
        api_key_dict['provider_website'] = provider_info.get('website')
        api_key_dict['provider_display_name'] = provider_info.get('name')
        api_key_dict['provider_logo_path'] = provider_info.get('logo_path')
        api_keys.append(api_key_dict)
    
    return api_keys


async def disable_shared_api_key(session: Session, api_key_id: int, user_id: int) -> SharedAPIKey:
    """
    Disable a shared API key and remove it from LiteLLM
    
    Args:
        session: Database session
        api_key_id: API key ID to disable
        user_id: User ID (for authorization check)
        
    Returns:
        Updated SharedAPIKey
        
    Raises:
        HTTPException: If API key not found, not owned by user, or LiteLLM sync fails
    """
    # Get API key and verify ownership
    statement = select(SharedAPIKey).where(
        SharedAPIKey.id == api_key_id,
        SharedAPIKey.user_id == user_id
    )
    api_key = session.exec(statement).first()
    
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found or you don't have permission to modify it"
        )
    
    # Check if already inactive
    if api_key.status == APIKeyStatus.INACTIVE:
        return api_key
    
    # Get user info for LiteLLM sync
    user_statement = select(User).where(User.id == user_id)
    user = session.exec(user_statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store original status for rollback
    original_status = api_key.status
    
    # Update status to INACTIVE
    api_key.status = APIKeyStatus.INACTIVE
    api_key.updated_at = datetime.utcnow()
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    
    # Sync with LiteLLM - delete the model and credential (skip in testing)
    if not settings.TESTING:
        try:
            credential_name = f"{api_key.provider.value}/{user.email}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Delete model from LiteLLM if model_id exists
                if api_key.litellm_model_id:
                    # Check if model exists before deleting
                    model_check_response = await client.get(
                        f"{settings.LITELLM_BASE_URL}/models/{api_key.litellm_model_id}",
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    if model_check_response.status_code == 500:
                        print(f"LiteLLM model check failed with 500: {model_check_response.text}")
                    
                    if model_check_response.status_code == 200:
                        delete_response = await client.post(
                            f"{settings.LITELLM_BASE_URL}/model/delete",
                            json={"id": api_key.litellm_model_id},
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
            api_key.status = original_status
            api_key.updated_at = datetime.utcnow()
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync disable with LiteLLM: {str(e)}"
            )
    
    # Log the disable action
    log_api_key_usage(
        db=session,
        user_id=user_id,
        api_key_id=str(api_key_id),
        action=APIKeyAction.SHARED,
        details=f"Disabled {api_key.provider.value} API key"
    )
    
    return api_key


async def enable_shared_api_key(session: Session, api_key_id: int, user_id: int) -> SharedAPIKey:
    """
    Enable a shared API key and add it back to LiteLLM
    
    Args:
        session: Database session
        api_key_id: API key ID to enable
        user_id: User ID (for authorization check)
        
    Returns:
        Updated SharedAPIKey
        
    Raises:
        HTTPException: If API key not found, not owned by user, or LiteLLM sync fails
    """
    # Get API key and verify ownership
    statement = select(SharedAPIKey).where(
        SharedAPIKey.id == api_key_id,
        SharedAPIKey.user_id == user_id
    )
    api_key = session.exec(statement).first()
    
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found or you don't have permission to modify it"
        )
    
    # Check if already active
    if api_key.status == APIKeyStatus.ACTIVE:
        return api_key
    
    # Cannot enable revoked API keys
    if api_key.status == APIKeyStatus.REVOKED:
        raise HTTPException(
            status_code=400,
            detail="Cannot enable a revoked API key"
        )
    
    # Get user info for LiteLLM sync
    user_statement = select(User).where(User.id == user_id)
    user = session.exec(user_statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store original status for rollback
    original_status = api_key.status
    
    # Update status to ACTIVE
    api_key.status = APIKeyStatus.ACTIVE
    api_key.updated_at = datetime.utcnow()
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    
    # Sync with LiteLLM - recreate the model (skip in testing)
    if not settings.TESTING:
        try:
            # Decrypt API key to get plain text for LiteLLM
            plain_api_key = decrypt_token(api_key.encrypted_api_key)
            model_id = await _sync_to_litellm(user, api_key.provider, plain_api_key)
            api_key.litellm_model_id = model_id
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
            
        except Exception as e:
            # Rollback status change if LiteLLM sync fails
            api_key.status = original_status
            api_key.updated_at = datetime.utcnow()
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync enable with LiteLLM: {str(e)}"
            )
    
    # Log the enable action
    log_api_key_usage(
        db=session,
        user_id=user_id,
        api_key_id=str(api_key_id),
        action=APIKeyAction.SHARED,
        details=f"Enabled {api_key.provider.value} API key"
    )
    
    return api_key


async def delete_shared_api_key(session: Session, api_key_id: int, user_id: int) -> None:
    """
    Delete a shared API key and remove it from LiteLLM
    
    This operation is idempotent for repeated deletion of the same API key,
    but will return 404 if trying to delete an API key that doesn't exist
    or belongs to another user (for security).
    
    Args:
        session: Database session
        api_key_id: API key ID to delete
        user_id: User ID (for authorization check)
        
    Raises:
        HTTPException: If API key not found/not owned by user, or LiteLLM sync fails
    """
    # Get API key and verify ownership
    statement = select(SharedAPIKey).where(
        SharedAPIKey.id == api_key_id,
        SharedAPIKey.user_id == user_id
    )
    api_key = session.exec(statement).first()
    
    # Return 404 for non-existent or unauthorized access
    # This is important for security - don't reveal if an api_key_id exists
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found or you don't have permission to delete it"
        )
    
    # Get user info for LiteLLM sync
    user_statement = select(User).where(User.id == user_id)
    user = session.exec(user_statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Sync with LiteLLM - delete model and credential (skip in testing)
    if not settings.TESTING:
        try:
            credential_name = f"{api_key.provider.value}/{user.email}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if model exists before deleting
                if api_key.litellm_model_id:
                    model_check_response = await client.get(
                        f"{settings.LITELLM_BASE_URL}/models/{api_key.litellm_model_id}",
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    if model_check_response.status_code == 500:
                        print(f"LiteLLM model check failed with 500: {model_check_response.text}")
                    
                    if model_check_response.status_code == 200:
                        # Delete model from LiteLLM
                        delete_model_response = await client.post(
                            f"{settings.LITELLM_BASE_URL}/model/delete",
                            json={"id": api_key.litellm_model_id},
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
    log_api_key_usage(
        db=session,
        user_id=user_id,
        api_key_id=str(api_key_id),
        action=APIKeyAction.SHARED,
        details=f"Deleted {api_key.provider.value} API key"
    )
    
    # Delete from database
    session.delete(api_key)
    session.commit()


def get_shared_api_key_metrics(session: Session, api_key_id: int, user_id: int) -> Dict:
    """
    Get metrics for a shared API key (currently returns mock data)
    
    Args:
        session: Database session
        api_key_id: API key ID
        user_id: User ID for authorization check
        
    Returns:
        Dict with metrics data (total_tokens, total_duration_days, total_requests, chart_data)
        
    Raises:
        HTTPException: If API key not found or user doesn't own it
    """
    # Verify ownership
    statement = select(SharedAPIKey).where(
        SharedAPIKey.id == api_key_id,
        SharedAPIKey.user_id == user_id
    )
    api_key = session.exec(statement).first()
    
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found"
        )
    
    # Generate mock chart data - 48 hours of random values
    chart_data = []
    for i in range(48):
        hour = (datetime.now() - timedelta(hours=47-i)).strftime("%Y-%m-%d %H:00")
        value = random.randint(20, 100)
        chart_data.append({"date": hour, "value": value})
    
    return {
        "total_tokens": 592.5,
        "total_duration_days": 2.5,
        "total_requests": 45,
        "chart_data": chart_data
    }
