"""
Webhook router for LiteLLM callbacks
"""
from fastapi import APIRouter, HTTPException, status, Request
from typing import Dict, Any
import redis
from dotenv import load_dotenv
import os

from api.schemas.litellm_callback import LiteLLMCallbackRequest, WebhookResponse
from api.services.litellm_callback_service import enqueue_callback
from api.config import settings

load_dotenv("../.env")
REDIS_ENV = os.getenv("REDIS_DATABASE", "redis://redis:6379/")

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/litellm/success", response_model=WebhookResponse)
async def litellm_success_callback(
    callback_data: Dict[str, Any],
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
        callback_data: Raw callback JSON from LiteLLM
        request: FastAPI request object

    Returns:
        WebhookResponse confirming receipt

    Raises:
        HTTPException 400: Invalid callback data
        HTTPException 503: Redis connection failed
    """
    try:
        # Parse callback data
        callback = LiteLLMCallbackRequest(**callback_data)

        # Connect to Redis and enqueue (use sync client for enqueue operation)
        redis_client = redis.from_url(REDIS_ENV, encoding="utf-8", decode_responses=True)

        try:
            success = enqueue_callback(redis_client, callback_data)
            redis_client.close()

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to queue callback for processing"
                )

            return WebhookResponse(success=True, message="Callback received and queued")

        except redis.ConnectionError as e:
            redis_client.close()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Redis connection failed: {str(e)}"
            )

    except Exception as e:
        # Validation error or other issue
        if "validation" in str(e).lower() or "field" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid callback data: {str(e)}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing callback: {str(e)}"
        )


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoints"""
    return {"status": "healthy", "service": "webhooks"}
