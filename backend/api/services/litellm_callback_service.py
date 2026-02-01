"""
Service layer for processing LiteLLM success callbacks

Handles:
- Enqueuing callbacks to Redis
- Processing callbacks from queue
- Updating token statistics
"""
import json
import logging
from typing import Dict, Any, Optional

from sqlmodel import Session, select
from sqlalchemy import text

from api.models.user import User
from api.models.shared_api_key import SharedAPIKey
from api.models.subscription import Subscription
from api.schemas.litellm_callback import LiteLLMCallbackRequest

logger = logging.getLogger(__name__)

# Redis queue key
CALLBACK_QUEUE_KEY = "litellm:callbacks:success"


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
        # Serialize to JSON and push to list
        json_data = json.dumps(callback_data)
        redis_client.lpush(CALLBACK_QUEUE_KEY, json_data)
        logger.info(f"Enqueued callback to Redis: {callback_data.get('model_id')}")
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


def parse_callback_data(data: Dict[str, Any]) -> Optional[LiteLLMCallbackRequest]:
    """
    Parse callback data into schema

    Args:
        data: Raw callback data dict

    Returns:
        Parsed LiteLLMCallbackRequest or None if validation fails
    """
    try:
        return LiteLLMCallbackRequest(**data)
    except Exception as e:
        logger.error(f"Failed to parse callback data: {e}")
        return None


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
    callback: LiteLLMCallbackRequest,
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
        # Update consumer's consumed_tokens atomically
        session.execute(
            text(f"UPDATE users SET consumed_tokens = consumed_tokens + {total_tokens} WHERE id = {consumer_user.id}")
        )

        # If subscription exists, update contributor and shared API key stats
        if subscription:
            # Update shared API key stats atomically
            session.execute(
                text(f"UPDATE shared_api_keys SET total_requests = total_requests + 1, total_tokens = total_tokens + {total_tokens} WHERE id = {subscription.shared_api_key_id}")
            )

            # Update contributor's contributed_tokens atomically
            session.execute(
                text(f"UPDATE users SET contributed_tokens = contributed_tokens + {total_tokens} WHERE id = {subscription.user_id}")
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
        # Find consumer by api_key_hash
        consumer = find_user_by_api_key_hash(session, callback.user_api_key_hash)
        if not consumer:
            logger.warning(
                f"No consumer found for api_key_hash: {callback.user_api_key_hash}"
            )
            # Don't fail - just log and continue

        # Find subscription by model_id
        subscription = find_subscription_by_model_id(session, callback.model_id)
        if not subscription:
            logger.warning(f"No subscription found for model_id: {callback.model_id}")
            # Don't fail - just log and continue

        # Update statistics
        if consumer:
            return update_token_statistics(session, callback, consumer, subscription)
        else:
            # No consumer found, can't update stats
            return True

    except Exception as e:
        logger.error(f"Error processing callback: {e}")
        return False
