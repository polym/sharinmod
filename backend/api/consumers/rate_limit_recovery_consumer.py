#!/usr/bin/env python3
"""
Rate Limit Recovery Consumer

Periodically checks for SharedAPIKey with expired rate_limit_reset_at
and automatically reactivates them by rebinding the user's selected models.

Run with: python -m api.consumers.rate_limit_recovery_consumer

Graceful shutdown: SIGTERM or SIGINT (Ctrl+C)
"""
import signal
import sys
import json
import logging
import time
from typing import Optional
from datetime import datetime, timezone

from dotenv import load_dotenv
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from sqlmodel import Session, select
from api.database import engine
from api.models.shared_api_key import SharedAPIKey, APIKeyStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Check interval in seconds
CHECK_INTERVAL = 60

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


def recover_expired_keys(session: Session) -> int:
    """
    Check and recover expired rate-limited keys

    Args:
        session: Database session

    Returns:
        Number of keys recovered
    """
    now = datetime.now(timezone.utc)
    statement = select(SharedAPIKey).where(
        SharedAPIKey.status == APIKeyStatus.INACTIVE,
        SharedAPIKey.rate_limit_reset_at != None,
        SharedAPIKey.rate_limit_reset_at <= now
    )
    keys = session.exec(statement).all()

    recovered = 0
    for key in keys:
        try:
            logger.info(
                f"Recovering SharedAPIKey {key.id}, "
                f"reset time was {key.rate_limit_reset_at}"
            )

            # Update status back to active
            key.status = APIKeyStatus.ACTIVE

            # Clear rate limit fields
            key.rate_limit_reset_at = None
            key.rate_limit_models_backup = None
            session.add(key)
            session.commit()

            recovered += 1
            logger.info(f"Successfully recovered SharedAPIKey {key.id}")
        except Exception as e:
            logger.error(f"Failed to recover key {key.id}: {e}")
            session.rollback()

    return recovered


def main():
    """Main consumer loop"""
    logger.info("Starting rate limit recovery consumer...")

    # Setup signal handlers
    setup_signals()

    # Main processing loop
    logger.info(f"Consumer ready, checking every {CHECK_INTERVAL} seconds...")
    total_recovered = 0

    try:
        while not shutdown_requested:
            # Create a new database session for each check
            session = Session(engine)

            try:
                # Check and recover expired keys
                recovered = recover_expired_keys(session)
                if recovered > 0:
                    total_recovered += recovered
                    logger.info(f"Recovered {recovered} keys this cycle, total: {total_recovered}")
            except Exception as e:
                logger.error(f"Error in recovery cycle: {e}", exc_info=True)
            finally:
                session.close()

            # Wait for next check (interruptible by shutdown signal)
            for _ in range(CHECK_INTERVAL):
                if shutdown_requested:
                    break
                time.sleep(1)

    except Exception as e:
        logger.error(f"Fatal error in consumer loop: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info(f"Consumer shutdown. Total recovered: {total_recovered}")


if __name__ == "__main__":
    main()
