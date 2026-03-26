"""
Webhook router for LiteLLM callbacks
"""
from fastapi import APIRouter, HTTPException, status, Request, Depends
import redis
from dotenv import load_dotenv
import os
import json
import logging
from typing import List
from pydantic import ValidationError
from sqlmodel import Session, select

from api.database import get_db
from api.schemas.litellm_callback import (
    LiteLLMSpendlogCallbackRequest,
    WebhookResponse
)
from api.services.litellm_callback_service import (
    enqueue_callback,
    find_user_by_api_key_hash,
    find_subscription_by_model_id
)
from api.config import settings

logger = logging.getLogger(__name__)

# Truncation marker for log output
TRUNCATION_MARKER = "... [truncated] ... "


def truncate_json_str(json_str: str) -> str:
    """
    Truncate a JSON string in the middle if it exceeds MAX_LOG_TRUNCATE_LENGTH.

    Args:
        json_str: The JSON string to potentially truncate

    Returns:
        Truncated string with "... [truncated] ..." in the middle,
        or the original string if under the limit
    """
    if len(json_str) <= settings.MAX_LOG_TRUNCATE_LENGTH:
        return json_str
    half = (settings.MAX_LOG_TRUNCATE_LENGTH - len(TRUNCATION_MARKER)) // 2
    return json_str[:half] + TRUNCATION_MARKER + json_str[-half:]


load_dotenv("../.env")
REDIS_ENV = os.getenv("REDIS_DATABASE", "redis://redis:6379/")

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/litellm/spendlog", response_model=WebhookResponse)
async def litellm_spendlog_callback(
    request: Request
):
    """
    Receive LiteLLM spendlog callback and enqueue for processing

    This is a unified endpoint that handles both success and failure callbacks:
    1. Receives callback data from LiteLLM after API calls (success or failure)
    2. Validates the callback data (all fields are optional)
    3. Enqueues the data to Redis for asynchronous processing
    4. Returns immediately (fire-and-forget pattern)

    The consumer processes callbacks based on the status field:
    - status="success": Update token statistics + create success usage log
    - status="failure": Create failure usage log only (no token statistics)
    - status missing: Default to success behavior

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
        logger.info("[WEBHOOK] Received LiteLLM spendlog callback request")
        logger.info(f"[WEBHOOK] Raw request body:\n{json.dumps(callback_data, indent=2, ensure_ascii=False)}")
        logger.info("=" * 80)

        # Handle both single object and array of callbacks
        callbacks_to_process: List[LiteLLMSpendlogCallbackRequest] = []
        if isinstance(callback_data, list):
            logger.info(f"[WEBHOOK] Received array of {len(callback_data)} callback(s)")
            for i, item in enumerate(callback_data):
                logger.debug(f"[WEBHOOK] Validating callback #{i+1}")
                callback = LiteLLMSpendlogCallbackRequest(**item)
                callbacks_to_process.append(callback)
        else:
            logger.info("[WEBHOOK] Received single callback")
            callback = LiteLLMSpendlogCallbackRequest(**callback_data)
            callbacks_to_process.append(callback)

        logger.info(f"[WEBHOOK] Successfully validated {len(callbacks_to_process)} callback(s)")

        # Debug log: show validated callbacks with truncation
        truncated_callbacks: List[str] = []
        for callback in callbacks_to_process:
            json_str = json.dumps(callback.model_dump(), indent=2, ensure_ascii=False)
            truncated_callbacks.append(truncate_json_str(json_str))
        logger.debug(f"Validated callbacks: {truncated_callbacks}")

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
