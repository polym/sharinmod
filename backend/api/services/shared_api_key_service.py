from sqlmodel import Session, select
from api.models.shared_api_key import SharedAPIKey, APIKeyProvider, APIKeyStatus
from api.models.user import User
from api.models.subscription import Subscription
from api.utils.encryption import encrypt_token, decrypt_token
from api.services.api_key_validation_service import validate_api_key
from api.services.api_key_usage_service import log_api_key_usage
from api.models.api_key_usage import APIKeyAction
from api.config import settings
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException
import httpx
import json
import random


def _handle_litellm_response(response, operation_name: str) -> bool:
    """
    Handle LiteLLM API response with unified error handling

    Args:
        response: httpx.Response object
        operation_name: Description of the operation for logging

    Returns:
        True if operation succeeded (2xx or 404)

    Raises:
        httpx.HTTPStatusError: If response status code is not 2xx or 404
    """
    print(f"[{operation_name}] Response status: {response.status_code}")
    print(f"[{operation_name}] Response body: {response.text}")

    if 200 <= response.status_code < 300:
        return True
    elif response.status_code == 404:
        print(f"[{operation_name}] Object not found (404), treating as success")
        return True
    else:
        print(f"[{operation_name}] Unexpected status code: {response.status_code}")
        response.raise_for_status()


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


async def _sync_to_litellm(user: User, provider: APIKeyProvider, api_key: str) -> Dict[str, str]:
    """
    Sync shared API key to LiteLLM by creating credential and all supported models

    Args:
        user: User object with litellm_user_id
        provider: API key provider
        api_key: Plain text API key

    Returns:
        Dict mapping model_name to litellm_model_id

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

    # Get supported models for this provider
    supported_models = PROVIDER_INFO[provider]["supported_models"]
    if not supported_models:
        raise ValueError(f"No supported models configured for provider: {provider.value}")
    if not supported_models:
        raise ValueError(f"No supported models configured for provider: {provider.value}")

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
        _handle_litellm_response(credential_check_response, "CREDENTIAL_CHECK")

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
            _handle_litellm_response(credential_response, "CREDENTIAL_UPDATE")
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
            _handle_litellm_response(credential_response, "CREDENTIAL_CREATE")

        # Step 2: Create all models in LiteLLM
        model_ids = {}
        for model_name in supported_models:
            model_payload = {
                "model_name": model_name,
                "litellm_params": {
                    "custom_llm_provider": "anthropic",
                    "litellm_credential_name": credential_name,
                    "model": model_name
                },
                "provider": "anthropic",
                "litellm_model_name": model_name,
            }

            print(f"[MODEL_CREATE] Creating model '{model_name}' with payload:", json.dumps(model_payload, indent=2))

            model_response = await client.post(
                f"{settings.LITELLM_BASE_URL}/model/new",
                json=model_payload,
                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
            )
            _handle_litellm_response(model_response, f"MODEL_CREATE_{model_name}")

            response_data = model_response.json()
            model_ids[model_name] = response_data["model_id"]
            print(f"[MODEL_CREATE] Model '{model_name}' created with ID: {model_ids[model_name]}")

        return model_ids


async def _create_models_for_credential(
    user: User,
    provider: APIKeyProvider,
    credential_name: str
) -> Dict[str, str]:
    """
    Create all supported models for an existing credential in LiteLLM

    Args:
        user: User object
        provider: API key provider
        credential_name: Name of the existing credential

    Returns:
        Dict mapping model_name to litellm_model_id

    Raises:
        Exception: If LiteLLM API calls fail
    """
    supported_models = PROVIDER_INFO[provider]["supported_models"]
    if not supported_models:
        raise ValueError(f"No supported models configured for provider: {provider.value}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        model_ids = {}
        for model_name in supported_models:
            model_payload = {
                "model_name": model_name,
                "litellm_params": {
                    "custom_llm_provider": "anthropic",
                    "litellm_credential_name": credential_name,
                    "model": model_name
                },
                "provider": "anthropic",
                "litellm_model_name": model_name,
            }

            print(f"[ENABLE_MODEL_CREATE] Creating model '{model_name}' with payload:", json.dumps(model_payload, indent=2))

            model_response = await client.post(
                f"{settings.LITELLM_BASE_URL}/model/new",
                json=model_payload,
                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
            )
            _handle_litellm_response(model_response, f"ENABLE_MODEL_CREATE_{model_name}")

            response_data = model_response.json()
            model_ids[model_name] = response_data["model_id"]
            print(f"[ENABLE_MODEL_CREATE] Model '{model_name}' created with ID: {model_ids[model_name]}")

        return model_ids


async def create_shared_api_key(
    session: Session,
    user: User,
    provider: APIKeyProvider,
    api_key: str,
    api_key_metadata: Optional[str] = None
) -> Dict[str, Any]:
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
    
    # Sync with LiteLLM (create credential and models) - skip in testing
    if not settings.TESTING:
        try:
            model_ids = await _sync_to_litellm(user, provider, api_key)
            # Store all model IDs as JSON
            shared_api_key.litellm_model_ids = json.dumps(model_ids)
            # Keep first model ID for backward compatibility
            first_model = list(model_ids.keys())[0]
            shared_api_key.litellm_model_id = model_ids[first_model]
            session.add(shared_api_key)
            session.commit()
            session.refresh(shared_api_key)
            
            # Create subscriptions for all models
            for model_name, model_id in model_ids.items():
                subscription = Subscription(
                    model_id=model_id,
                    shared_api_key_id=shared_api_key.id,
                    user_id=user.id
                )
                session.add(subscription)
            session.commit()
            
        except Exception as e:
            # Rollback local API key creation if LiteLLM sync fails
            session.rollback()
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
    
    # Sync with LiteLLM - delete models only, keep credential (skip in testing)
    if not settings.TESTING:
        try:
            # Parse model IDs from JSON
            model_ids = {}
            if api_key.litellm_model_ids:
                try:
                    model_ids = json.loads(api_key.litellm_model_ids)
                except json.JSONDecodeError:
                    print(f"[DISABLE] Failed to parse litellm_model_ids: {api_key.litellm_model_ids}")
                    model_ids = {}

            # Delete all models
            async with httpx.AsyncClient(timeout=10.0) as client:
                for model_name, litellm_model_id in model_ids.items():
                    print(f"[DISABLE] Deleting model '{model_name}' with ID: {litellm_model_id}")
                    delete_response = await client.post(
                        f"{settings.LITELLM_BASE_URL}/model/delete",
                        json={"id": litellm_model_id},
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    _handle_litellm_response(delete_response, f"DISABLE_MODEL_DELETE_{model_name}")

                # For backward compatibility, also delete the old single model_id if exists
                if api_key.litellm_model_id and api_key.litellm_model_id not in model_ids.values():
                    print(f"[DISABLE] Deleting legacy model with ID: {api_key.litellm_model_id}")
                    delete_response = await client.post(
                        f"{settings.LITELLM_BASE_URL}/model/delete",
                        json={"id": api_key.litellm_model_id},
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    _handle_litellm_response(delete_response, "DISABLE_LEGACY_MODEL_DELETE")

            # Clear model ID fields
            api_key.litellm_model_ids = None
            api_key.litellm_model_id = None
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
            
            # Delete related subscriptions since models are no longer available
            subscription_statement = select(Subscription).where(
                Subscription.shared_api_key_id == api_key_id
            )
            subscriptions = session.exec(subscription_statement).all()
            for subscription in subscriptions:
                session.delete(subscription)
            session.commit()

        except Exception as e:
            # Rollback status change if LiteLLM sync fails
            print(f"[DISABLE] Exception during LiteLLM sync: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"[DISABLE] Traceback: {traceback.format_exc()}")
            session.rollback()
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
    
    # Sync with LiteLLM - recreate all models (skip in testing)
    if not settings.TESTING:
        try:
            credential_name = f"{api_key.provider.value}/{user.email}"
            try:
                model_ids = await _create_models_for_credential(user, api_key.provider, credential_name)
            except Exception as credential_error:
                # Credential may have been externally deleted, recreate it with models
                print(f"[ENABLE] Credential creation failed, attempting full recreate: {credential_error}")
                plain_api_key = decrypt_token(api_key.encrypted_api_key)
                model_ids = await _sync_to_litellm(user, api_key.provider, plain_api_key)
            # Store all model IDs as JSON
            api_key.litellm_model_ids = json.dumps(model_ids)
            # Keep first model ID for backward compatibility
            first_model = list(model_ids.keys())[0]
            api_key.litellm_model_id = model_ids[first_model]
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
            
            # Recreate subscriptions for all models since they are now available again
            for model_name, model_id in model_ids.items():
                subscription = Subscription(
                    model_id=model_id,
                    shared_api_key_id=api_key.id,
                    user_id=user.id
                )
                session.add(subscription)
            session.commit()

        except Exception as e:
            # Rollback status change if LiteLLM sync fails
            session.rollback()
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
    
    # Sync with LiteLLM - delete models first, then credential (skip in testing)
    # NOTE: Delete models FIRST, then credential to avoid orphaned models
    if not settings.TESTING:
        try:
            credential_name = f"{api_key.provider.value}/{user.email}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                # Step 1: Delete all models FIRST
                model_ids = {}
                if api_key.litellm_model_ids:
                    try:
                        model_ids = json.loads(api_key.litellm_model_ids)
                    except json.JSONDecodeError:
                        print(f"[DELETE] Failed to parse litellm_model_ids: {api_key.litellm_model_ids}")
                        model_ids = {}

                for model_name, litellm_model_id in model_ids.items():
                    print(f"[DELETE] Deleting model '{model_name}' with ID: {litellm_model_id}")
                    delete_response = await client.post(
                        f"{settings.LITELLM_BASE_URL}/model/delete",
                        json={"id": litellm_model_id},
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    _handle_litellm_response(delete_response, f"DELETE_MODEL_{model_name}")

                # For backward compatibility, also delete the old single model_id if exists
                if api_key.litellm_model_id and api_key.litellm_model_id not in model_ids.values():
                    print(f"[DELETE] Deleting legacy model with ID: {api_key.litellm_model_id}")
                    delete_response = await client.post(
                        f"{settings.LITELLM_BASE_URL}/model/delete",
                        json={"id": api_key.litellm_model_id},
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    _handle_litellm_response(delete_response, "DELETE_LEGACY_MODEL")

                # Step 2: Delete credential SECOND
                print(f"[DELETE] Deleting credential: {credential_name}")
                delete_credential_response = await client.delete(
                    f"{settings.LITELLM_BASE_URL}/credentials/{credential_name}",
                    headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                )
                _handle_litellm_response(delete_credential_response, "DELETE_CREDENTIAL")

        except Exception as e:
            # Don't delete database record if LiteLLM sync fails
            print(f"[DELETE] Exception during LiteLLM sync: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"[DELETE] Traceback: {traceback.format_exc()}")
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
    
    # Delete related subscriptions first
    subscription_statement = select(Subscription).where(
        Subscription.shared_api_key_id == api_key_id
    )
    subscriptions = session.exec(subscription_statement).all()
    for subscription in subscriptions:
        session.delete(subscription)
    
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
