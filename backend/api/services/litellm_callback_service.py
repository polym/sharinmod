"""
Service layer for processing LiteLLM success callbacks

Handles:
- Enqueuing callbacks to Redis
- Processing callbacks from queue
- Updating token statistics
"""
import json
import logging
import redis
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime

from sqlmodel import Session, select
from sqlalchemy import text

from api.models.user import User
from api.models.shared_api_key import SharedAPIKey
from api.models.subscription import Subscription
from api.schemas.litellm_callback import LiteLLMSpendlogCallbackRequest

logger = logging.getLogger(__name__)

# Redis queue key
CALLBACK_QUEUE_KEY = "litellm:callbacks:spendlog"

# Thread-local storage for Redis client
_redis_local = threading.local()
_redis_client_lock = threading.Lock()


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get or create thread-local Redis client with proper locking

    Returns:
        redis.Redis client or None if connection fails
    """
    # Check thread-local storage first
    if hasattr(_redis_local, 'client') and _redis_local.client is not None:
        return _redis_local.client

    with _redis_client_lock:
        # Double-check after acquiring lock
        if hasattr(_redis_local, 'client') and _redis_local.client is not None:
            return _redis_local.client

        try:
            from api.config import settings
            client = redis.from_url(
                settings.REDIS_DATABASE,
                encoding="utf-8",
                decode_responses=True
            )
            client.ping()
            _redis_local.client = client
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            _redis_local.client = None
    return _redis_local.client


def close_redis_client():
    """
    Close the Redis client for current thread.
    Should be called during cleanup/shutdown.
    """
    if hasattr(_redis_local, 'client') and _redis_local.client is not None:
        try:
            _redis_local.client.close()
        except Exception as e:
            logger.error(f"Failed to close Redis client: {e}")
        finally:
            _redis_local.client = None


def enqueue_callback(redis_client, callback_data: Dict[str, Any]) -> bool:
    """
    Enqueue callback data to Redis queue

    Args:
        redis_client: Redis client instance
        callback_data: Callback data dict

    Returns:
        True if enqueued successfully, False otherwise
    """
    try:
        # Extract model_id for logging
        model_id = callback_data.get('model_id') or callback_data.get('hidden_params', {}).get('model_id', 'unknown')

        # Serialize to JSON and push to list
        json_data = json.dumps(callback_data)
        redis_client.lpush(CALLBACK_QUEUE_KEY, json_data)
        logger.info(f"Enqueued callback to Redis: model_id={model_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to enqueue callback: {e}")
        return False


def dequeue_callback(redis_client, timeout: int = 0) -> Optional[Dict[str, Any]]:
    """
    Dequeue callback data from Redis queue (blocking)

    Args:
        redis_client: Redis client instance
        timeout: Block timeout in seconds (0 = block indefinitely)

    Returns:
        Callback data dict or None
    """
    try:
        result = redis_client.brpop(CALLBACK_QUEUE_KEY, timeout=timeout)
        if result:
            _, json_data = result
            return json.loads(json_data)
        return None
    except Exception as e:
        logger.error(f"Failed to dequeue callback: {e}")
        return None


def parse_callback_data(data: Dict[str, Any]) -> Optional[LiteLLMSpendlogCallbackRequest]:
    """
    Parse callback data into schema

    Args:
        data: Raw callback data dict

    Returns:
        Parsed LiteLLMSpendlogCallbackRequest or None if validation fails
    """
    try:
        return LiteLLMSpendlogCallbackRequest(**data)
    except Exception as e:
        logger.error(f"Failed to parse callback data: {e}")
        return None


def extract_api_key_hash(callback: LiteLLMSpendlogCallbackRequest) -> Optional[str]:
    """
    Extract user_api_key_hash from callback data

    The hash may be in metadata.user_api_key_hash

    Args:
        callback: Parsed callback data

    Returns:
        API key hash or None
    """
    if callback.metadata and callback.metadata.user_api_key_hash:
        return callback.metadata.user_api_key_hash
    return None


def extract_model_id(callback: LiteLLMSpendlogCallbackRequest) -> Optional[str]:
    """
    Extract model_id from callback data

    The model_id may be at root level or in hidden_params

    Args:
        callback: Parsed callback data

    Returns:
        Model ID or None
    """
    if callback.model_id:
        return callback.model_id
    if callback.hidden_params and callback.hidden_params.model_id:
        return callback.hidden_params.model_id
    return None


def extract_client_from_request_tags(request_tags: Optional[List[str]]) -> Optional[str]:
    """
    Extract client name from request_tags by parsing User-Agent strings

    The request_tags array contains User-Agent strings like:
    ["User-Agent: Mozilla", "User-Agent: Mozilla/5.0 (Macintosh...)"]

    Args:
        request_tags: Array of tag strings from LiteLLM callback

    Returns:
        Client name (Zed, Claude-Code, Chrome, Safari, Firefox) or None
    """
    if not request_tags:
        return None

    # Find the longest User-Agent string (contains the full browser info)
    user_agent = None
    for tag in request_tags:
        if tag and "User-Agent:" in tag:
            # Use the longer string which contains the full User-Agent
            if user_agent is None or len(tag) > len(user_agent):
                user_agent = tag.lower()

    if not user_agent:
        return None

    user_agent = user_agent.split("/")[0].replace("user-agent: ", "")

    # Parse User-Agent to identify client
    if "zed" in user_agent:
        return "Zed"
    elif "claude" in user_agent:
        return "Claude-Code"
    elif ("chrome" in user_agent or "mozilla" in user_agent) and "edg" not in user_agent:
        return "Chrome"
    elif "safari" in user_agent and "chrome" not in user_agent:
        return "Safari"
    elif "firefox" in user_agent:
        return "Firefox"

    return user_agent


def find_user_by_api_key_hash(session: Session, api_key_hash: str) -> Optional[User]:
    """
    Find user by their unified API key hash (token_id from LiteLLM)

    Args:
        session: Database session
        api_key_hash: Token ID/hash from LiteLLM callback

    Returns:
        User object or None
    """
    try:
        from api.models.unified_api_key import UnifiedAPIKey

        statement = select(UnifiedAPIKey).where(
            UnifiedAPIKey.api_key_hash == api_key_hash
        )
        unified_key = session.exec(statement).first()

        if unified_key:
            # Get the user who owns this unified key
            user_statement = select(User).where(User.id == unified_key.user_id)
            return session.exec(user_statement).first()

        return None
    except Exception as e:
        logger.error(f"Failed to find user by api_key_hash: {e}")
        return None


def find_subscription_by_model_id(session: Session, model_id: str) -> Optional[Subscription]:
    """
    Find subscription by model_id

    Args:
        session: Database session
        model_id: LiteLLM model identifier

    Returns:
        Subscription object or None
    """
    try:
        statement = select(Subscription).where(Subscription.model_id == model_id)
        return session.exec(statement).first()
    except Exception as e:
        logger.error(f"Failed to find subscription by model_id: {e}")
        return None


def update_token_statistics(
    session: Session,
    callback: LiteLLMSpendlogCallbackRequest,
    consumer_user: User,
    subscription: Optional[Subscription] = None
) -> bool:
    """
    Update token statistics for all parties involved using atomic UPDATE operations

    Uses raw SQL to prevent race conditions when multiple consumers process callbacks concurrently.

    Args:
        session: Database session
        callback: Parsed callback data
        consumer_user: User who consumed the tokens
        subscription: Subscription linking to contributor (optional)

    Returns:
        True if update successful, False otherwise
    """
    try:
        total_tokens = callback.total_tokens

        # Use atomic UPDATE operations to prevent race conditions
        # Update consumer's consumed_tokens atomically (using bind params to prevent SQL injection)
        session.execute(
            text("UPDATE users SET consumed_tokens = consumed_tokens + :tokens WHERE id = :user_id"),
            {"tokens": total_tokens, "user_id": consumer_user.id}
        )

        # If subscription exists, update contributor and shared API key stats
        if subscription:
            # Update Redis Hash for hourly statistics BEFORE database commit
            # This ensures Redis data is consistent with database state
            redis_client = get_redis_client()
            if redis_client:
                hour_key = datetime.utcnow().strftime("%Y%m%d%H")
                redis_key = f"sharinmod:subscription:{subscription.id}:hourly_tokens"
                try:
                    # Only set TTL if this is a new key (optimization)
                    is_new_key = not redis_client.exists(redis_key)
                    redis_client.hincrby(redis_key, hour_key, total_tokens)
                    if is_new_key:
                        redis_client.expire(redis_key, 50 * 3600)  # 50 hours TTL
                    logger.debug(f"Updated Redis Hash: {redis_key}, hour: {hour_key}, tokens: {total_tokens}")
                except Exception as e:
                    logger.error(f"Failed to update Redis Hash: {e}")
                    # Don't fail the entire operation if Redis update fails

            # Update shared API key stats atomically (using bind params to prevent SQL injection)
            session.execute(
                text("UPDATE shared_api_keys SET total_requests = total_requests + 1, total_tokens = total_tokens + :tokens WHERE id = :key_id"),
                {"tokens": total_tokens, "key_id": subscription.shared_api_key_id}
            )

            # Update contributor's contributed_tokens atomically (using bind params to prevent SQL injection)
            session.execute(
                text("UPDATE users SET contributed_tokens = contributed_tokens + :tokens WHERE id = :user_id"),
                {"tokens": total_tokens, "user_id": subscription.user_id}
            )

        session.commit()
        logger.info(
            f"Updated token stats: consumer={consumer_user.email}, "
            f"tokens={total_tokens}"
        )
        return True

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to update token statistics: {e}")
        return False


def process_callback(session: Session, callback_data: Dict[str, Any]) -> bool:
    """
    Process a single callback from the queue

    Handles both success and failure callbacks:
    - status="success" (or missing): Update token statistics + create success usage log
    - status="failure": Create failure usage log only (no token statistics update)

    Args:
        session: Database session
        callback_data: Raw callback data dict

    Returns:
        True if processed successfully, False otherwise
    """
    # Parse callback data
    callback = parse_callback_data(callback_data)
    if not callback:
        logger.error(f"Invalid callback data: {callback_data}")
        return False

    try:
        # Extract api_key_hash from callback (from metadata)
        api_key_hash = extract_api_key_hash(callback)
        if not api_key_hash:
            logger.warning("No api_key_hash found in callback metadata")
            # Don't fail - just log and continue

        # Extract model_id from callback (root or hidden_params)
        model_id = extract_model_id(callback)
        if not model_id:
            logger.warning(f"No model_id found in callback for model={callback.model}")

        # Extract client from request_tags (User-Agent)
        request_tags = callback_data.get('request_tags')
        client = extract_client_from_request_tags(request_tags)

        # Find consumer by api_key_hash
        consumer = None
        unified_api_key_id = None
        unified_api_key_name = None

        if api_key_hash:
            consumer = find_user_by_api_key_hash(session, api_key_hash)
            if consumer:
                # Get unified API key info
                from api.models.unified_api_key import UnifiedAPIKey
                from sqlmodel import select

                key_statement = select(UnifiedAPIKey).where(
                    UnifiedAPIKey.api_key_hash == api_key_hash
                )
                unified_key = session.exec(key_statement).first()
                if unified_key:
                    unified_api_key_id = unified_key.id
                    unified_api_key_name = unified_key.api_key_name

        if not consumer:
            logger.warning(f"No consumer found for api_key_hash: {api_key_hash}")
            # Don't fail - just log and continue

        # Find subscription by model_id
        subscription = None
        if model_id:
            subscription = find_subscription_by_model_id(session, model_id)
        if not subscription:
            logger.warning(f"No subscription found for model_id: {model_id}")
            # Don't fail - just log and continue

        # Determine callback status (default to success if not specified)
        # Validate status field - only accept "success" or "failure"
        callback_status = callback.status
        if callback_status and callback_status not in ("success", "failure"):
            logger.warning(f"Invalid status value '{callback_status}', defaulting to 'success'")
            callback_status = "success"
        callback_status = callback_status if callback_status else "success"

        # Handle based on callback status
        if callback_status == "failure":
            # Failure callback: create failure usage log only
            if consumer:
                try:
                    from api.services.usage_log_service import create_failure_usage_log
                    from api.models.usage_log import UsageLogKind

                    # Determine kind: own (contributor), shared (consumer), or direct (no subscription)
                    kind = UsageLogKind.DIRECT
                    if subscription:
                        if subscription.user_id == consumer.id:
                            kind = UsageLogKind.OWN  # User is the contributor
                        else:
                            kind = UsageLogKind.SHARED  # User is consuming someone else's API key

                    create_failure_usage_log(
                        db=session,
                        user_id=consumer.id,
                        model=callback.model,
                        error_message=callback.error_message,
                        model_id=model_id,
                        unified_api_key_id=unified_api_key_id,
                        unified_api_key_name=unified_api_key_name,
                        kind=kind
                    )
                    logger.info(f"Created failure usage log for user {consumer.id}, kind={kind}")
                except Exception as e:
                    logger.error(f"Failed to create failure usage log: {e}")
                    # Log full callback data for manual recovery
                    logger.error(f"Lost failure callback data: {json.dumps(callback_data, ensure_ascii=False)}")
                    return False

            return True
        else:
            # Success callback (or default): update token statistics + create success usage log
            if consumer:
                stats_updated = update_token_statistics(session, callback, consumer, subscription)

                # Create usage log (don't fail if this errors)
                if stats_updated:
                    try:
                        from api.services.usage_log_service import create_usage_log
                        create_usage_log(session, consumer.id, callback, subscription, client)
                    except Exception as e:
                        logger.error(f"Failed to create usage log (non-critical): {e}")

                return stats_updated
            else:
                # No consumer found, can't update stats
                return True

    except Exception as e:
        logger.error(f"Error processing callback: {e}")
        return False
