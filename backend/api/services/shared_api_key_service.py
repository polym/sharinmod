from sqlmodel import Session, select
from api.models.shared_api_key import SharedAPIKey, APIKeyStatus
from api.models.user import User
from api.models.subscription import Subscription
from api.models.provider_config import ProviderModel
from api.utils.encryption import encrypt_token, decrypt_token
from api.services.api_key_validation_service import validate_api_key
from api.services.api_key_usage_service import log_api_key_usage
from api.models.api_key_usage import APIKeyAction
from api.config import settings
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from collections import defaultdict
import httpx
import json
import random
import redis
import logging
import urllib.parse

logger = logging.getLogger(__name__)


def _get_base_model_name(model_name: str) -> str:
    """
    Remove @public or @org-{id} suffix from model name if present

    Args:
        model_name: Model name that may contain @public or @org-{id} suffix

    Returns:
        Base model name without the organization suffix
    """
    if model_name.endswith('@public'):
        return model_name[:-7]  # Remove '@public' suffix (7 chars)
    if '@org-' in model_name:
        return model_name.rsplit('@org-', 1)[0]
    return model_name


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
    # For credential delete operations, 403 might mean credential is in use or other permissions issue
    # Treat it as success for idempotency, but log a warning
    elif response.status_code == 403 and "DELETE" in operation_name:
        print(f"[{operation_name}] 403 Forbidden - credential may be in use, treating as success for idempotency")
        return True
    else:
        print(f"[{operation_name}] Unexpected status code: {response.status_code}")
        response.raise_for_status()


def _handle_litellm_delete_response(response, operation_name: str) -> bool:
    """
    Handle LiteLLM delete model API response with lenient error handling

    Args:
        response: httpx.Response object
        operation_name: Description of the operation for logging

    Returns:
        True if operation succeeded or model doesn't exist (idempotent)

    Note:
        For delete operations, 404 (model not found) is treated as success (idempotent).
        400 errors are logged but don't raise exception to allow continuation.
    """
    print(f"[{operation_name}] Response status: {response.status_code}")
    print(f"[{operation_name}] Response body: {response.text}")

    if 200 <= response.status_code < 300:
        return True
    elif response.status_code == 404:
        print(f"[{operation_name}] Model not found (404), treating as success (idempotent)")
        return True
    elif response.status_code == 400:
        print(f"[{operation_name}] Bad request (400) - model may be in use or invalid, continuing...")
        return True  # Continue anyway for robustness
    else:
        print(f"[{operation_name}] Unexpected status code: {response.status_code}")
        # For delete operations, be more lenient
        print(f"[{operation_name}] Continuing despite error for robustness")
        return True




def check_provider_api_key_exists(session: Session, user_id: int, provider: str, organization_id: Optional[int] = None) -> bool:
    """
    Check if user already has an API key for this provider

    Args:
        session: Database session
        user_id: User ID
        provider: API key provider
        organization_id: Optional organization ID for isolation
            - None: check in public workspace only
            - int: check in specific organization only

    Returns:
        True if API key exists for this provider in this scope, False otherwise
    """
    conditions = [
        SharedAPIKey.user_id == user_id,
        SharedAPIKey.provider == provider
    ]
    if organization_id is not None:
        # Filter by specific organization
        conditions.append(SharedAPIKey.organization_id == organization_id)
    else:
        # Public workspace only: organization_id IS NULL
        conditions.append(SharedAPIKey.organization_id.is_(None))

    statement = select(SharedAPIKey).where(*conditions)
    result = session.exec(statement).first()
    return result is not None


async def _sync_to_litellm(user: User, provider: str, api_key: str, selected_models: Optional[List[str]] = None, organization_id: Optional[int] = None) -> Dict[str, str]:
    """
    Sync shared API key to LiteLLM by creating credential and all supported models

    Args:
        user: User object with litellm_user_id
        provider: API key provider
        api_key: Plain text API key
        selected_models: Optional list of models to create. If None, create all supported models.
        organization_id: Optional organization ID for namespace isolation

    Returns:
        Dict mapping model_name to litellm_model_id

    Raises:
        Exception: If LiteLLM API calls fail
    """
    # Prepare credential and model data with organization suffix
    if organization_id:
        credential_name = f"{provider}/{user.email}/org-{organization_id}"
    else:
        credential_name = f"{provider}/{user.email}/public"

    # Look up provider configuration from database (dynamic providers only)
    from api.services.provider_config_service import get_provider_by_key
    from api.models.provider_config import ProviderModel as ProviderModelDB
    from api.database import engine
    from sqlmodel import Session as SyncSession

    with SyncSession(engine) as _db:
        provider_config = get_provider_by_key(_db, provider)
        if not provider_config or not provider_config.base_url:
            print(f"[SYNC_TO_LITELLM] Provider {provider} not configured or has no base_url, skipping LiteLLM sync")
            return {}
        api_base = provider_config.base_url
        custom_provider = provider_config.custom_llm_provider or "openai"
        db_models_q = select(ProviderModelDB.model_key, ProviderModelDB.real_model).where(
            ProviderModelDB.provider_config_id == provider_config.id,
            ProviderModelDB.is_enabled == True
        )
        supported_models = list(_db.exec(db_models_q).all())  # 返回 (model_key, real_model) 元组列表

    # 将元组列表转换为 model_key 列表以支持正确的模型验证
    supported_model_keys = [m[0] for m in supported_models]

    if not api_base:
        raise ValueError(f"No API base URL configured for provider: {provider}")

    # Verify user has LiteLLM user ID
    if not user.litellm_user_id:
        raise ValueError(f"User {user.email} does not have a LiteLLM user ID")

    if not supported_models:
        raise ValueError(f"No supported models configured for provider: {provider}")

    # Use selected models if provided, otherwise use all supported models
    models_to_create = selected_models if selected_models else supported_model_keys

    # Validate selected models - 使用 model_key 列表进行比较
    invalid_models = [m for m in models_to_create if m not in supported_model_keys]
    if invalid_models:
        raise ValueError(f"Invalid models for provider {provider}: {invalid_models}")

    # 确保至少有一个有效模型
    if not models_to_create or (isinstance(models_to_create, list) and len(models_to_create) == 0):
        raise ValueError(f"No valid models to create for provider {provider}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Step 1: Check if credential exists, update if exists, create if not
        credential_payload = {
            "credential_values": {
                "api_key": api_key,
                "api_base": api_base
            },
            "credential_info": {
                "custom_llm_provider": custom_provider
            }
        }

        # Check if credential exists
        # URL encode the credential name to handle special characters like @
        encoded_credential_name = urllib.parse.quote(credential_name, safe="/")
        credential_check_response = await client.get(
            f"{settings.LITELLM_BASE_URL}/credentials/by_name/{encoded_credential_name}",
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
                f"{settings.LITELLM_BASE_URL}/credentials/{encoded_credential_name}",
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

        # Step 2: Create selected models in LiteLLM
        model_ids = {}
        # 构建 model_key 到 real_model 的映射
        real_model_map = {m[0]: m[1] for m in supported_models}

        for model_name in models_to_create:
            # 从映射中查找 real_model
            real_model_val = real_model_map.get(model_name)
            # 如果没有 real_model，使用 model_name
            actual_real_model = real_model_val if real_model_val else model_name
            litellm_model = f"openrouter/openrouter/{actual_real_model}" if provider == "openrouter" else actual_real_model
            # Add organization suffix to model_name for isolation
            model_name_with_org = f"{model_name}@org-{organization_id}" if organization_id else f"{model_name}@public"
            model_payload = {
                "model_name": model_name_with_org,
                "litellm_params": {
                    "custom_llm_provider": custom_provider,
                    "litellm_credential_name": credential_name,
                    "model": litellm_model
                },
                "provider": custom_provider,
                "litellm_model_name": litellm_model,
            }

            print(f"[MODEL_CREATE] Creating model '{model_name_with_org}' with litellm_model '{litellm_model}'", json.dumps(model_payload, indent=2))

            print(f"[MODEL_CREATE] Creating model '{model_name}' with litellm_model '{litellm_model}'", json.dumps(model_payload, indent=2))

            model_response = await client.post(
                f"{settings.LITELLM_BASE_URL}/model/new",
                json=model_payload,
                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
            )
            _handle_litellm_response(model_response, f"MODEL_CREATE_{model_name}")

            response_data = model_response.json()
            model_ids[model_name_with_org] = response_data["model_id"]
            print(f"[MODEL_CREATE] Model '{model_name_with_org}' created with ID: {model_ids[model_name_with_org]}")

        return model_ids


async def _create_models_for_credential(
    user: User,
    provider: str,
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
    # Look up provider configuration from database
    from api.services.provider_config_service import get_provider_by_key
    from api.models.provider_config import ProviderModel as ProviderModelDB
    from api.database import engine
    from sqlmodel import Session as SyncSession

    with SyncSession(engine) as _db:
        provider_config = get_provider_by_key(_db, provider)
        if not provider_config:
            raise ValueError(f"Provider {provider} not found in database")

        custom_provider = provider_config.custom_llm_provider or "openai"
        db_models_q = select(ProviderModelDB.model_key, ProviderModelDB.real_model).where(
            ProviderModelDB.provider_config_id == provider_config.id,
            ProviderModelDB.is_enabled == True
        )
        supported_models = list(_db.exec(db_models_q).all())  # 返回 (model_key, real_model) 元组列表

    if not supported_models:
        raise ValueError(f"No supported models configured for provider: {provider}")

    # 构建 model_key 到 real_model 的映射
    real_model_map = {m[0]: m[1] for m in supported_models}

    async with httpx.AsyncClient(timeout=10.0) as client:
        model_ids = {}
        for model_key, real_model in supported_models:
            # 如果没有 real_model，使用 model_key
            actual_real_model = real_model if real_model else model_key
            # For OpenRouter: pony-alpha -> openrouter/pony-alpha -> openrouter/openrouter/pony-alpha
            litellm_model = f"openrouter/openrouter/{actual_real_model}" if provider == "openrouter" else actual_real_model
            model_payload = {
                "model_name": model_key,
                "litellm_params": {
                    "custom_llm_provider": custom_provider,
                    "litellm_credential_name": credential_name,
                    "model": litellm_model
                },
                "provider": custom_provider,
                "litellm_model_name": litellm_model,
            }

            print(f"[ENABLE_MODEL_CREATE] Creating model '{model_key}' with payload:", json.dumps(model_payload, indent=2))

            model_response = await client.post(
                f"{settings.LITELLM_BASE_URL}/model/new",
                json=model_payload,
                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
            )
            _handle_litellm_response(model_response, f"ENABLE_MODEL_CREATE_{model_key}")

            response_data = model_response.json()
            model_ids[model_key] = response_data["model_id"]
            print(f"[ENABLE_MODEL_CREATE] Model '{model_key}' created with ID: {model_ids[model_key]}")

        return model_ids


async def create_shared_api_key(
    session: Session,
    user: User,
    provider: str,
    api_key: str,
    api_key_metadata: Optional[str] = None,
    selected_models: Optional[List[str]] = None,
    organization_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a new shared API key with validation

    Args:
        session: Database session
        user: Current authenticated user
        provider: API key provider
        api_key: Plain text API key to share
        api_key_metadata: Optional metadata JSON string
        selected_models: Optional list of models to bind. If None, bind all supported models.
        organization_id: Optional organization ID for isolation

    Returns:
        Dict with created API key info and validation result

    Raises:
        HTTPException: If duplicate provider or validation fails
    """
    # Check if user already has an API key for this provider in this organization
    if check_provider_api_key_exists(session, user.id, provider, organization_id):
        raise HTTPException(
            status_code=400,
            detail=f"You already have an API key for {provider}. Each account can only add one API key per provider per organization."
        )

    # Validate API key with provider API
    validation_result = await validate_api_key(provider, api_key, session)

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
        organization_id=organization_id,
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
            logger.info(f"[CREATE] Syncing to LiteLLM: provider={provider}, user={user.email}, models={selected_models}, org_id={organization_id}")
            model_ids = await _sync_to_litellm(user, provider, api_key, selected_models, organization_id)
            logger.info(f"[CREATE] LiteLLM sync result: {list(model_ids.keys()) if model_ids else 'skipped (dynamic provider without base_url)'}")

            # Helper function to remove organization suffix from model name
            def get_base_model_name(model_name: str) -> str:
                """Remove @public or @org-{id} suffix from model name if present"""
                if model_name.endswith('@public'):
                    return model_name[:-7]  # Remove '@public' suffix (7 chars)
                if '@org-' in model_name:
                    return model_name.rsplit('@org-', 1)[0]
                return model_name

            # model_ids == {} means dynamic provider that skips LiteLLM sync
            if not model_ids:
                # For dynamic providers, get models from database and create subscriptions
                from api.services.provider_config_service import get_provider_by_key
                from sqlmodel import select
                from api.models.provider_config import ProviderModel

                provider_config = get_provider_by_key(session, provider)
                if provider_config:
                    # Get enabled models from database
                    models_statement = select(ProviderModel.model_key).where(
                        ProviderModel.provider_config_id == provider_config.id,
                        ProviderModel.is_enabled == True
                    )
                    db_models = session.exec(models_statement).all()

                    # Filter by selected_models if provided
                    if selected_models:
                        db_models = [m for m in db_models if m in selected_models]

                    # Create subscriptions for each model (using model_key as model_id for dynamic providers)
                    for model_key in db_models:
                        subscription = Subscription(
                            model_id=model_key,  # Use model_key directly for dynamic providers
                            shared_api_key_id=shared_api_key.id,
                            user_id=user.id,
                            organization_id=organization_id
                        )
                        session.add(subscription)
                    session.commit()

                    # Store model keys in litellm_model_ids for tracking
                    shared_api_key.litellm_model_ids = json.dumps({m: m for m in db_models})
                    if db_models:
                        shared_api_key.litellm_model_id = db_models[0]
                    # Persist user's model selection (survives disable/enable cycles)
                    # Store base model names (without @org-{id} suffix)
                    shared_api_key.user_selected_models = json.dumps(list(db_models))
                    logger.info(f"[CREATE] Saved user_selected_models (dynamic): {list(db_models)}")
                    session.add(shared_api_key)
                    session.commit()
                    session.refresh(shared_api_key)
            else:
                # Static provider - use LiteLLM model IDs
                # Store all model IDs as JSON
                shared_api_key.litellm_model_ids = json.dumps(model_ids)
                # Keep first model ID for backward compatibility
                first_model = list(model_ids.keys())[0]
                shared_api_key.litellm_model_id = model_ids[first_model]
                # Persist user's model selection (survives disable/enable cycles)
                # Store base model names (without @org-{id} suffix)
                base_model_names = [_get_base_model_name(m) for m in model_ids.keys()]
                shared_api_key.user_selected_models = json.dumps(base_model_names)
                logger.info(f"[CREATE] Saved user_selected_models (static): {base_model_names}")
                session.add(shared_api_key)
                session.commit()
                session.refresh(shared_api_key)

                # Create subscriptions for all models
                for model_name, model_id in model_ids.items():
                    subscription = Subscription(
                        model_id=model_id,
                        shared_api_key_id=shared_api_key.id,
                        user_id=user.id,
                        organization_id=organization_id
                    )
                    session.add(subscription)
                session.commit()

        except Exception as e:
            # Rollback local API key creation if LiteLLM sync fails
            # First, delete any subscriptions that were created
            try:
                subscription_statement = select(Subscription).where(
                    Subscription.shared_api_key_id == shared_api_key.id
                )
                subscriptions = session.exec(subscription_statement).all()
                for subscription in subscriptions:
                    session.delete(subscription)
                session.commit()
            except Exception:
                session.rollback()

            # Then delete the API key itself
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
        details=f"Shared {provider} API key"
    )

    return {
        "api_key": shared_api_key,
        "validation": validation_result
    }


def get_user_shared_api_keys(session: Session, user_id: int, organization_id: Optional[int] = None) -> List[Dict]:
    """
    Get all shared API keys for a user with provider info

    Args:
        session: Database session
        user_id: User ID
        organization_id: Optional organization ID for filtering
            - None: only return public workspace (organization_id IS NULL)
            - int: only return subscriptions for that organization

    Returns:
        List of dicts compatible with SharedAPIKeyResponse (with provider info)
    """
    conditions = [SharedAPIKey.user_id == user_id]
    if organization_id is not None:
        # Filter by specific organization
        conditions.append(SharedAPIKey.organization_id == organization_id)
    else:
        # Public workspace only: organization_id IS NULL
        conditions.append(SharedAPIKey.organization_id.is_(None))

    statement = select(SharedAPIKey).where(*conditions).order_by(
        SharedAPIKey.created_at.desc()
    )

    results = session.exec(statement).all()

    # Convert to dicts and add provider info
    api_keys = []
    for api_key in results:
        api_key_dict = api_key.model_dump()
        # Get provider info from database
        from api.services.provider_config_service import get_provider_by_key
        provider_config = get_provider_by_key(session, api_key.provider)
        if provider_config:
            provider_info = {
                "name": provider_config.name,
                "website": provider_config.website,
                "logo_path": provider_config.logo_path,
                "supported_models": []  # Will be loaded from database separately
            }
        else:
            provider_info = {}

        # Get actual bound models from litellm_model_ids
        bound_models = []
        if api_key.litellm_model_ids:
            try:
                model_ids = json.loads(api_key.litellm_model_ids)
                # Return base model names (without @org-{id} suffix) for display
                bound_models = [_get_base_model_name(m) for m in model_ids.keys()]
            except json.JSONDecodeError:
                pass

        api_key_dict['supported_models'] = bound_models  # Actual bound models (base names)
        api_key_dict['provider_website'] = provider_info.get('website')
        api_key_dict['provider_display_name'] = provider_info.get('name')
        api_key_dict['provider_logo_path'] = provider_info.get('logo_path')
        api_keys.append(api_key_dict)

    return api_keys


async def disable_shared_api_key(session: Session, api_key_id: int, user_id: int, organization_id: Optional[int] = None) -> SharedAPIKey:
    """
    Disable a shared API key and remove it from LiteLLM

    Args:
        session: Database session
        api_key_id: API key ID to disable
        user_id: User ID (for authorization check)
        organization_id: Optional organization ID for credential name

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
    api_key.updated_at = datetime.now(timezone.utc)
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
                    _handle_litellm_delete_response(delete_response, f"DISABLE_MODEL_DELETE_{model_name}")

                # For backward compatibility, also delete the old single model_id if exists
                if api_key.litellm_model_id and api_key.litellm_model_id not in model_ids.values():
                    print(f"[DISABLE] Deleting legacy model with ID: {api_key.litellm_model_id}")
                    delete_response = await client.post(
                        f"{settings.LITELLM_BASE_URL}/model/delete",
                        json={"id": api_key.litellm_model_id},
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    _handle_litellm_delete_response(delete_response, "DISABLE_LEGACY_MODEL_DELETE")

            # Clear live LiteLLM model IDs (user_selected_models is intentionally kept
            # so enable_shared_api_key can restore the exact models the user chose)
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
            api_key.updated_at = datetime.now(timezone.utc)
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
        details=f"Disabled {api_key.provider} API key"
    )
    
    return api_key


async def enable_shared_api_key(session: Session, api_key_id: int, user_id: int, organization_id: Optional[int] = None) -> SharedAPIKey:
    """
    Enable a shared API key and add it back to LiteLLM

    Args:
        session: Database session
        api_key_id: API key ID to enable
        user_id: User ID (for authorization check)
        organization_id: Optional organization ID for credential name

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
    api_key.updated_at = datetime.now(timezone.utc)
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    
    # Sync with LiteLLM - recreate user-selected models (skip in testing)
    if not settings.TESTING:
        try:
            # Restore user's previously selected models
            saved_models = None
            if api_key.user_selected_models:
                try:
                    saved_models = json.loads(api_key.user_selected_models)
                    logger.info(f"[ENABLE] Restoring user-selected models: {saved_models}")
                except json.JSONDecodeError:
                    logger.warning(f"[ENABLE] Failed to parse user_selected_models: {api_key.user_selected_models!r}, falling back to provider defaults")

            # Decrypt key and re-sync to LiteLLM (handles both static and dynamic providers)
            plain_api_key = decrypt_token(api_key.encrypted_api_key)
            logger.info(f"[ENABLE] Syncing to LiteLLM: provider={api_key.provider}, user={user.email}, models={saved_models}, org_id={api_key.organization_id}")
            model_ids = await _sync_to_litellm(user, api_key.provider, plain_api_key, saved_models, api_key.organization_id)
            logger.info(f"[ENABLE] LiteLLM sync result: {list(model_ids.keys()) if model_ids else 'skipped (dynamic provider without base_url)'}")

            if not model_ids:
                # Dynamic provider without LiteLLM - recreate subscriptions from DB
                from api.services.provider_config_service import get_provider_by_key
                provider_config = get_provider_by_key(session, api_key.provider)
                if provider_config:
                    models_statement = select(ProviderModel).where(
                        ProviderModel.provider_config_id == provider_config.id,
                        ProviderModel.is_enabled == True
                    )
                    db_model_keys = [m.model_key for m in session.exec(models_statement).all()]
                    if saved_models:
                        db_model_keys = [m for m in db_model_keys if m in saved_models]
                    logger.info(f"[ENABLE] Dynamic provider, recreating subscriptions for: {db_model_keys}")
                    for model_key in db_model_keys:
                        subscription = Subscription(
                            model_id=model_key,
                            shared_api_key_id=api_key.id,
                            user_id=user.id,
                            organization_id=api_key.organization_id
                        )
                        session.add(subscription)
                    session.commit()
                    api_key.litellm_model_ids = json.dumps({m: m for m in db_model_keys})
                    api_key.litellm_model_id = db_model_keys[0] if db_model_keys else None
                    session.add(api_key)
                    session.commit()
                    session.refresh(api_key)
                else:
                    logger.warning(f"[ENABLE] Dynamic provider {api_key.provider} config not found, skipping subscription recreation")
            else:
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
                        user_id=user.id,
                        organization_id=api_key.organization_id
                    )
                    session.add(subscription)
                session.commit()

        except Exception as e:
            # Rollback status change if LiteLLM sync fails
            session.rollback()
            api_key.status = original_status
            api_key.updated_at = datetime.now(timezone.utc)
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
        details=f"Enabled {api_key.provider} API key"
    )
    
    return api_key


async def delete_shared_api_key(session: Session, api_key_id: int, user_id: int, organization_id: Optional[int] = None) -> None:
    """
    Delete a shared API key and remove it from LiteLLM

    This operation is idempotent for repeated deletion of the same API key,
    but will return 404 if trying to delete an API key that doesn't exist
    or belongs to another user (for security).

    Args:
        session: Database session
        api_key_id: API key ID to delete
        user_id: User ID (for authorization check)
        organization_id: Optional organization ID for credential name

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
            if api_key.organization_id:
                credential_name = f"{api_key.provider}/{user.email}/org-{api_key.organization_id}"
            else:
                credential_name = f"{api_key.provider}/{user.email}/public"

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
                    _handle_litellm_delete_response(delete_response, f"DELETE_MODEL_{model_name}")

                # For backward compatibility, also delete the old single model_id if exists
                if api_key.litellm_model_id and api_key.litellm_model_id not in model_ids.values():
                    print(f"[DELETE] Deleting legacy model with ID: {api_key.litellm_model_id}")
                    delete_response = await client.post(
                        f"{settings.LITELLM_BASE_URL}/model/delete",
                        json={"id": api_key.litellm_model_id},
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    _handle_litellm_delete_response(delete_response, "DELETE_LEGACY_MODEL")

                # Step 2: Delete credential SECOND
                # URL encode the credential name to handle special characters like @
                encoded_credential_name = urllib.parse.quote(credential_name, safe="/")
                print(f"[DELETE] Deleting credential: {credential_name} (encoded: {encoded_credential_name})")
                delete_credential_response = await client.delete(
                    f"{settings.LITELLM_BASE_URL}/credentials/{encoded_credential_name}",
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
        details=f"Deleted {api_key.provider} API key"
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


def get_subscription_hourly_tokens(session: Session, shared_api_key_id: int, hours: int = 48) -> List[Dict[str, Any]]:
    """
    Get hourly token usage for all subscriptions linked to a shared API key

    Args:
        session: Database session
        shared_api_key_id: Shared API key ID
        hours: Number of hours to look back (default 48, max 168)

    Returns:
        List of dicts with 'date' and 'value' keys
    """
    # Validate hours parameter to prevent performance issues
    if hours < 1:
        logger.warning(f"Invalid hours value: {hours}, using minimum of 1")
        hours = 1
    elif hours > 168:  # Max 7 days
        logger.warning(f"Hours value {hours} exceeds maximum of 168, using maximum")
        hours = 168

    # Get all subscriptions for this shared API key
    statement = select(Subscription).where(
        Subscription.shared_api_key_id == shared_api_key_id
    )
    subscriptions = session.exec(statement).all()

    if not subscriptions:
        return []

    # Aggregate hourly data from Redis
    hourly_totals = defaultdict(int)

    try:
        redis_client = redis.from_url(
            settings.REDIS_DATABASE,
            encoding="utf-8",
            decode_responses=True
        )

        now = datetime.now(timezone.utc)
        for i in range(hours):
            hour_dt = now - timedelta(hours=hours - 1 - i)
            hour_key = hour_dt.strftime("%Y%m%d%H")

            for subscription in subscriptions:
                redis_key = f"sharinmod:subscription:{subscription.id}:hourly_tokens"
                value = redis_client.hget(redis_key, hour_key)
                if value:
                    hourly_totals[hour_dt] += int(value)

    except Exception as e:
        logger.error(f"Failed to get hourly tokens from Redis: {e}")
        return []

    # Convert to list of dicts (UTC time in RFC3339 format, frontend will handle timezone conversion)
    chart_data = []
    for hour_dt in sorted(hourly_totals.keys()):
        chart_data.append({
            "date": hour_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "value": hourly_totals[hour_dt]
        })

    # Fill missing hours with zeros (UTC time in RFC3339 format)
    result = []
    hour_dict = {item["date"]: item["value"] for item in chart_data}
    for i in range(hours):
        hour_dt = now - timedelta(hours=hours - 1 - i)
        date_str = hour_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        result.append({
            "date": date_str,
            "value": hour_dict.get(date_str, 0)
        })

    return result


def get_shared_api_key_metrics(session: Session, api_key_id: int, user_id: int) -> Dict:
    """
    Get metrics for a shared API key using real database data

    Args:
        session: Database session
        api_key_id: API key ID
        user_id: User ID for authorization check

    Returns:
        Dict with metrics data:
            - total_tokens (int): raw token value from database (frontend handles formatting)
            - total_duration_days (int): days since creation
            - total_requests (int): total request count from database
            - chart_data (list): mock 48-hour chart data

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

    # Calculate duration from creation date (use UTC for consistency)
    total_duration_days = (datetime.now(timezone.utc) - api_key.created_at).days

    # Get real hourly data from Redis
    chart_data = get_subscription_hourly_tokens(session, api_key.id)

    return {
        "total_tokens": api_key.total_tokens,
        "total_duration_days": total_duration_days,
        "total_requests": api_key.total_requests,
        "chart_data": chart_data
    }


async def update_shared_api_key(
    session: Session,
    api_key_id: int,
    user_id: int,
    new_api_key: Optional[str] = None,
    selected_models: Optional[List[str]] = None,
    organization_id: Optional[int] = None
) -> SharedAPIKey:
    """
    Update a shared API key (API Key and/or models)

    Args:
        session: Database session
        api_key_id: API key ID to update
        user_id: User ID for authorization check
        new_api_key: New API key to replace existing one (optional)
        selected_models: List of models to bind (required, at least one model)
        organization_id: Optional organization ID for credential name

    Returns:
        Updated SharedAPIKey

    Raises:
        HTTPException: If API key not found, validation fails, or LiteLLM sync fails
    """
    # Validate selected_models
    if not selected_models or len(selected_models) == 0:
        raise HTTPException(
            status_code=400,
            detail="请至少选择一个模型"
        )

    # Get API key and verify ownership
    statement = select(SharedAPIKey).where(
        SharedAPIKey.id == api_key_id,
        SharedAPIKey.user_id == user_id
    )
    api_key_obj = session.exec(statement).first()

    if not api_key_obj:
        raise HTTPException(
            status_code=404,
            detail="API key not found or you don't have permission to modify it"
        )

    # Get user info for LiteLLM sync
    user_statement = select(User).where(User.id == user_id)
    user = session.exec(user_statement).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate selected models against provider's supported models from database
    from api.services.provider_config_service import get_provider_by_key

    provider_config = get_provider_by_key(session, api_key_obj.provider)
    if not provider_config:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {api_key_obj.provider}"
        )

    # Load enabled models from database (include real_model)
    models_statement = select(ProviderModel.model_key, ProviderModel.real_model).where(
        ProviderModel.provider_config_id == provider_config.id,
        ProviderModel.is_enabled == True
    )
    db_models = session.exec(models_statement).all()
    supported_models = [m[0] for m in db_models]  # 只取 model_key 列表
    real_model_map = {m[0]: m[1] for m in db_models}  # model_key -> real_model 映射

    auto_removed_models = [m for m in selected_models if m not in supported_models]
    selected_models = [m for m in selected_models if m in supported_models]
    if auto_removed_models:
        logger.warning(f"[UPDATE] Auto-removing unsupported models for provider={api_key_obj.provider}: {auto_removed_models}")
    if not selected_models:
        raise HTTPException(
            status_code=400,
            detail=f"所有已选模型均不在当前供应商支持列表中，请重新选择。不支持的模型: {', '.join(auto_removed_models)}"
        )

    # Store original data for rollback
    original_api_key = api_key_obj.encrypted_api_key
    original_model_ids = api_key_obj.litellm_model_ids

    try:
        # Step 1: Update API Key if provided
        api_key_to_validate = None
        if new_api_key:
            # Validate new API key with provider API
            validation_result = await validate_api_key(api_key_obj.provider, new_api_key, session)
            if not validation_result["valid"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"API key validation failed: {validation_result['message']}"
                )
            # Encrypt new API key
            api_key_obj.encrypted_api_key = encrypt_token(new_api_key)
            api_key_to_validate = new_api_key  # 用于模型验证

        # Step 2: Calculate model differences
        current_model_ids = {}
        if api_key_obj.litellm_model_ids:
            try:
                current_model_ids = json.loads(api_key_obj.litellm_model_ids)
            except json.JSONDecodeError:
                current_model_ids = {}

        # Get base model names for comparison (without @org-{id} suffix)
        current_base_models = {_get_base_model_name(m): m for m in current_model_ids.keys()}

        # Models to remove (base model name in current but not in selected)
        models_to_remove = [current_base_models[base] for base in current_base_models if base not in selected_models]
        # Models to add (in selected but not in current)
        models_to_add = [m for m in selected_models if m not in current_base_models]

        # Step 3: Sync with LiteLLM (skip in testing)
        if not settings.TESTING:
            if api_key_obj.organization_id:
                credential_name = f"{api_key_obj.provider}/{user.email}/org-{api_key_obj.organization_id}"
            else:
                credential_name = f"{api_key_obj.provider}/{user.email}/public"
            # URL encode the credential name to handle special characters like @
            encoded_credential_name = urllib.parse.quote(credential_name, safe="/")

            # If new API key provided, update credential
            if new_api_key:
                # Look up provider configuration from database
                from api.services.provider_config_service import get_provider_by_key
                from api.database import engine
                from sqlmodel import Session as SyncSession
                with SyncSession(engine) as _db:
                    _pc = get_provider_by_key(_db, api_key_obj.provider)
                if not _pc or not _pc.base_url:
                    raise ValueError(f"Provider {api_key_obj.provider} has no base_url configured")
                api_base = _pc.base_url
                custom_provider = _pc.custom_llm_provider or "openai"

                if not api_base:
                    raise ValueError(f"No API base URL configured for provider: {api_key_obj.provider}")

                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Update credential with new API key
                    credential_payload = {
                        "credential_values": {
                            "api_key": new_api_key,
                            "api_base": api_base
                        },
                        "credential_info": {
                            "custom_llm_provider": custom_provider
                        }
                    }
                    update_payload = {
                        "credential_name": credential_name,
                        **credential_payload
                    }
                    credential_response = await client.patch(
                        f"{settings.LITELLM_BASE_URL}/credentials/{encoded_credential_name}",
                        json=update_payload,
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    _handle_litellm_response(credential_response, "UPDATE_CREDENTIAL")

            # Remove models no longer needed
            # Start with current models and remove the ones we don't want
            new_model_ids = current_model_ids.copy()
            for model_name in models_to_remove:
                new_model_ids.pop(model_name, None)

            if models_to_remove:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    for model_name in models_to_remove:
                        litellm_model_id = current_model_ids[model_name]
                        print(f"[UPDATE] Deleting model '{model_name}' with ID: {litellm_model_id}")
                        delete_response = await client.post(
                            f"{settings.LITELLM_BASE_URL}/model/delete",
                            json={"id": litellm_model_id},
                            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                        )
                        _handle_litellm_delete_response(delete_response, f"UPDATE_MODEL_DELETE_{model_name}")

            # Add new models
            if models_to_add:
                # Determine the custom_llm_provider from database
                from api.services.provider_config_service import get_provider_by_key
                from api.database import engine
                from sqlmodel import Session as SyncSession
                with SyncSession(engine) as _db:
                    _pc2 = get_provider_by_key(_db, api_key_obj.provider)
                custom_provider = (_pc2.custom_llm_provider or "openai") if _pc2 else "openai"

                async with httpx.AsyncClient(timeout=10.0) as client:
                    if api_key_obj.organization_id:
                        credential_name = f"{api_key_obj.provider}/{user.email}/org-{api_key_obj.organization_id}"
                    else:
                        credential_name = f"{api_key_obj.provider}/{user.email}/public"
                    for model_name in models_to_add:
                        # 获取 real_model，如果没有则使用 model_name
                        real_model_val = real_model_map.get(model_name) or model_name
                        # OpenRouter 特殊处理：添加 openrouter/openrouter/ 前缀
                        litellm_model = f"openrouter/openrouter/{real_model_val}" if api_key_obj.provider == "openrouter" else real_model_val
                        # Add organization suffix to model_name for isolation
                        model_name_with_org = f"{model_name}@org-{api_key_obj.organization_id}" if api_key_obj.organization_id else f"{model_name}@public"
                        model_payload = {
                            "model_name": model_name_with_org,
                            "litellm_params": {
                                "custom_llm_provider": custom_provider,
                                "litellm_credential_name": credential_name,
                                "model": litellm_model
                            },
                            "provider": custom_provider,
                            "litellm_model_name": litellm_model,
                        }
                        print(f"[UPDATE] Creating model '{model_name_with_org}' with litellm_model '{litellm_model}'")
                        model_response = await client.post(
                            f"{settings.LITELLM_BASE_URL}/model/new",
                            json=model_payload,
                            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                        )
                        _handle_litellm_response(model_response, f"UPDATE_MODEL_CREATE_{model_name}")
                        response_data = model_response.json()
                        new_model_ids[model_name_with_org] = response_data["model_id"]

            # Update litellm_model_ids
            api_key_obj.litellm_model_ids = json.dumps(new_model_ids)
            if new_model_ids:
                first_model = list(new_model_ids.keys())[0]
                api_key_obj.litellm_model_id = new_model_ids[first_model]
            else:
                api_key_obj.litellm_model_id = None

        # Step 4: Update database subscriptions
        # Delete subscriptions for removed models
        if models_to_remove:
            for model_name in models_to_remove:
                litellm_model_id = current_model_ids[model_name]
                subscription_statement = select(Subscription).where(
                    Subscription.shared_api_key_id == api_key_id,
                    Subscription.model_id == litellm_model_id
                )
                subscription = session.exec(subscription_statement).first()
                if subscription:
                    session.delete(subscription)

        # Add subscriptions for new models
        if models_to_add and api_key_obj.litellm_model_ids:
            updated_model_ids = json.loads(api_key_obj.litellm_model_ids)
            for model_name in models_to_add:
                model_name_with_org = f"{model_name}@org-{api_key_obj.organization_id}" if api_key_obj.organization_id else f"{model_name}@public"
                if model_name_with_org in updated_model_ids:
                    subscription = Subscription(
                        model_id=updated_model_ids[model_name_with_org],
                        shared_api_key_id=api_key_id,
                        user_id=user_id,
                        organization_id=api_key_obj.organization_id
                    )
                    session.add(subscription)

        # Persist updated model selection
        api_key_obj.user_selected_models = json.dumps(selected_models)
        logger.info(f"[UPDATE] Saved user_selected_models: {selected_models}")
        # Update timestamp
        api_key_obj.updated_at = datetime.now(timezone.utc)
        session.add(api_key_obj)
        session.commit()
        session.refresh(api_key_obj)

        return api_key_obj, auto_removed_models

    except Exception as e:
        # Rollback on error
        print(f"[UPDATE] Exception during update: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[UPDATE] Traceback: {traceback.format_exc()}")
        session.rollback()
        api_key_obj.encrypted_api_key = original_api_key
        api_key_obj.litellm_model_ids = original_model_ids
        session.add(api_key_obj)
        session.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update API key: {str(e)}"
        )
