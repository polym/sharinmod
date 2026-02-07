#!/usr/bin/env python3
"""
LiteLLM Callback Consumer

Standalone process that consumes LiteLLM callbacks (both success and failure) from Redis queue
and updates token statistics and creates usage logs.

Run with: python -m api.consumers.litellm_callback_consumer

Graceful shutdown: SIGTERM or SIGINT (Ctrl+C)
"""
import signal
import sys
import logging
import time
from typing import Optional

import redis
from dotenv import load_dotenv
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.database import Session, engine
from api.services.litellm_callback_service import (
    dequeue_callback,
    process_callback,
    CALLBACK_QUEUE_KEY
)
from api.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle SIGTERM and SIGINT for graceful shutdown"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


def setup_signals():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


def get_redis_client() -> Optional[redis.Redis]:
    """
    Create and return a Redis client

    Returns:
        redis.Redis client or None if connection fails
    """
    try:
        load_dotenv("../.env")
        redis_url = os.getenv("REDIS_DATABASE", "redis://redis:6379/")
        client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        # Test connection
        client.ping()
        logger.info(f"Connected to Redis: {redis_url}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None


def process_message(redis_client: redis.Redis, session: Session) -> bool:
    """
    Process a single callback message from the queue

    Args:
        redis_client: Redis client
        session: Database session

    Returns:
        True if message was processed, False if queue was empty
    """
    callback_data = dequeue_callback(redis_client, timeout=1)

    if callback_data is None:
        return False

    # Extract model_id for logging (may be at root or in hidden_params)
    model_id = callback_data.get('model_id') or callback_data.get('hidden_params', {}).get('model_id', callback_data.get('model', 'unknown'))
    logger.info(f"Processing callback: model_id={model_id}")

    try:
        success = process_callback(session, callback_data)
        if success:
            logger.info(f"Successfully processed callback for model_id={model_id}")
        else:
            logger.warning(f"Failed to process callback for model_id={model_id}")
        return True
    except Exception as e:
        logger.error(f"Error processing callback: {e}", exc_info=True)
        # Continue processing even if one message fails
        return True


def main():
    """Main consumer loop"""
    logger.info("Starting LiteLLM callback consumer...")

    # Setup signal handlers
    setup_signals()

    # Connect to Redis
    redis_client = get_redis_client()
    if not redis_client:
        logger.error("Failed to connect to Redis, exiting...")
        sys.exit(1)

    # Main processing loop
    logger.info("Consumer ready, waiting for callbacks...")
    processed_count = 0

    try:
        while not shutdown_requested:
            # Create a new database session for each message
            session = Session(engine)

            try:
                # Process one message
                if process_message(redis_client, session):
                    processed_count += 1
                    # Log progress every 100 messages
                    if processed_count % 100 == 0:
                        logger.info(f"Processed {processed_count} callbacks...")
            finally:
                session.close()

    except Exception as e:
        logger.error(f"Fatal error in consumer loop: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        redis_client.close()
        logger.info(f"Consumer shutdown. Total processed: {processed_count}")


if __name__ == "__main__":
    main()
