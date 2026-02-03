"""
Webhook router for LiteLLM callbacks
"""
from fastapi import APIRouter, HTTPException, status, Request, Depends
import redis
from dotenv import load_dotenv
import os
import json
import logging
from pydantic import ValidationError
from sqlmodel import Session, select

from api.database import get_db
from api.schemas.litellm_callback import (
    LiteLLMCallbackRequest,
    LiteLLMFailureCallbackRequest,
    WebhookResponse
)
from api.services.litellm_callback_service import (
    enqueue_callback,
    find_user_by_api_key_hash,
    find_subscription_by_model_id
)
from api.services.usage_log_service import create_failure_usage_log
from api.models.unified_api_key import UnifiedAPIKey

logger = logging.getLogger(__name__)

load_dotenv("../.env")
REDIS_ENV = os.getenv("REDIS_DATABASE", "redis://redis:6379/")

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/litellm/success", response_model=WebhookResponse)
async def litellm_success_callback(
    request: Request
):
    """
    Receive LiteLLM success callback and enqueue for processing

    This endpoint:
    1. Receives callback data from LiteLLM after successful API calls
    2. Validates the callback data
    3. Enqueues the data to Redis for asynchronous processing
    4. Returns immediately (fire-and-forget pattern)

    Protected by IP whitelist middleware (configured in app.py).

    Args:
        request: FastAPI request object

    Returns:
        WebhookResponse confirming receipt

    Raises:
        HTTPException 422: Invalid callback data
        HTTPException 503: Redis connection failed
    """
    try:
        # Get raw request body
        callback_data = await request.json()

        # Log raw request body for debugging
        logger.info("=" * 80)
        logger.info("[WEBHOOK] Received LiteLLM callback request")
        logger.info(f"[WEBHOOK] Raw request body:\n{json.dumps(callback_data, indent=2, ensure_ascii=False)}")
        logger.info("=" * 80)

        # Handle both single object and array of callbacks
        callbacks_to_process = []
        if isinstance(callback_data, list):
            logger.info(f"[WEBHOOK] Received array of {len(callback_data)} callback(s)")
            for i, item in enumerate(callback_data):
                logger.debug(f"[WEBHOOK] Validating callback #{i+1}")
                callback = LiteLLMCallbackRequest(**item)
                callbacks_to_process.append(callback)
        else:
            logger.info("[WEBHOOK] Received single callback")
            callback = LiteLLMCallbackRequest(**callback_data)
            callbacks_to_process.append(callback)

        logger.info(f"[WEBHOOK] Successfully validated {len(callbacks_to_process)} callback(s)")

        # Connect to Redis and enqueue (use sync client for enqueue operation)
        redis_client = redis.from_url(REDIS_ENV, encoding="utf-8", decode_responses=True)

        try:
            # Enqueue each validated callback
            enqueued_count = 0
            for callback in callbacks_to_process:
                # Convert to dict for JSON serialization
                callback_dict = callback.model_dump()
                success = enqueue_callback(redis_client, callback_dict)
                if success:
                    enqueued_count += 1

            redis_client.close()

            if enqueued_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to queue any callbacks for processing"
                )

            return WebhookResponse(
                success=True,
                message=f"Successfully received and queued {enqueued_count} callback(s)"
            )

        except redis.ConnectionError as e:
            redis_client.close()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Redis connection failed: {str(e)}"
            )

    except json.JSONDecodeError as e:
        logger.error(f"[WEBHOOK] JSON decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON in request body: {str(e)}"
        )
    except ValidationError as e:
        logger.error(f"[WEBHOOK] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid callback data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[WEBHOOK] Unexpected error: {str(e)}")
        # Re-raise HTTPExceptions
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing callback: {str(e)}"
        )


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoints"""
    return {"status": "healthy", "service": "webhooks"}


@router.post("/litellm/failure", response_model=WebhookResponse)
async def litellm_failure_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive LiteLLM failure callback and log the failure

    This endpoint:
    1. Receives failure callback data from LiteLLM
    2. Validates the callback data
    3. Creates a failure usage log entry
    4. Returns immediately

    Protected by IP whitelist middleware (configured in app.py).

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        WebhookResponse confirming receipt

    Raises:
        HTTPException 422: Invalid callback data
    """
    try:
        # Get raw request body
        callback_data = await request.json()

        # Log raw request body for debugging
        logger.info("=" * 80)
        logger.info("[WEBHOOK] Received LiteLLM failure callback request")
        logger.info(f"[WEBHOOK] Raw request body:\n{json.dumps(callback_data, indent=2, ensure_ascii=False)}")
        logger.info("=" * 80)

        # Validate failure callback
        failure_callback = LiteLLMFailureCallbackRequest(**callback_data)
        logger.info("[WEBHOOK] Successfully validated failure callback")

        # Extract api_key_hash from metadata
        api_key_hash = None
        if failure_callback.metadata:
            api_key_hash = failure_callback.metadata.user_api_key_hash

        # Extract model_id (root or hidden_params)
        model_id = failure_callback.model_id
        if not model_id and failure_callback.hidden_params:
            model_id = failure_callback.hidden_params.model_id

        # Find user and subscription
        user = None
        unified_api_key_id = None
        unified_api_key_name = None
        subscription_id = None

        if api_key_hash:
            user = find_user_by_api_key_hash(db, api_key_hash)
            if user:
                key_statement = select(UnifiedAPIKey).where(
                    UnifiedAPIKey.api_key_hash == api_key_hash
                )
                unified_key = db.exec(key_statement).first()
                if unified_key:
                    unified_api_key_id = unified_key.id
                    unified_api_key_name = unified_key.api_key_name

        if model_id:
            subscription = find_subscription_by_model_id(db, model_id)
            if subscription:
                subscription_id = subscription.id

        # Create failure usage log
        if user:
            create_failure_usage_log(
                db=db,
                user_id=user.id,
                model=failure_callback.model,
                error_message=failure_callback.error_message,
                model_id=model_id,
                unified_api_key_id=unified_api_key_id,
                unified_api_key_name=unified_api_key_name,
                subscription_id=subscription_id
            )
            logger.info(f"[WEBHOOK] Created failure usage log for user {user.id}")
        else:
            logger.warning("[WEBHOOK] No user found, skipping failure log creation")

        return WebhookResponse(
            success=True,
            message="Failure callback received"
        )

    except json.JSONDecodeError as e:
        logger.error(f"[WEBHOOK] JSON decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON in request body: {str(e)}"
        )
    except ValidationError as e:
        logger.error(f"[WEBHOOK] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid callback data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"[WEBHOOK] Unexpected error: {str(e)}")
        # Re-raise HTTPExceptions
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing failure callback: {str(e)}"
        )
