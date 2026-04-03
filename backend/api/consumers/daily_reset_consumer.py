#!/usr/bin/env python3
"""
Daily Reset Consumer

Standalone process that resets APIKey daily token limits at 00:00 (Asia/Shanghai).
- Resets daily_tokens_used to 0 for all keys
- Updates last_reset_date to today
- Recovers DAILY_LIMIT_EXCEEDED keys to ACTIVE status
- Creates history entries for recovery

Run with: python -m api.consumers.daily_reset_consumer

Graceful shutdown: SIGTERM or SIGINT (Ctrl+C)
"""
import os
import signal
import sys
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlmodel import Session, select

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.database import Session as DBSession, engine
from api.models.unified_api_key import UnifiedAPIKey, UnifiedAPIKeyStatus
from api.services.api_key_limit_history_service import create_limit_history_entry
from api.utils.datetime import get_today_in_timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Polling interval in seconds
POLL_INTERVAL = 60

# Timezone for daily reset (Asia/Shanghai = UTC+8)
RESET_TIMEZONE_OFFSET = timedelta(hours=8)

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


def get_shanghai_midnight_utc() -> datetime:
    """
    Get the next midnight in Asia/Shanghai timezone as UTC datetime.

    Returns:
        UTC datetime representing the next Shanghai midnight
    """
    # Get current time in Shanghai timezone
    now_utc = datetime.now(timezone.utc)
    shanghai_time = now_utc + RESET_TIMEZONE_OFFSET

    # Calculate tomorrow's midnight in Shanghai
    tomorrow_shanghai = shanghai_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    # Convert back to UTC
    tomorrow_utc = tomorrow_shanghai - RESET_TIMEZONE_OFFSET
    return tomorrow_utc


def should_run_daily_reset(last_run_time: Optional[datetime]) -> bool:
    """
    Check if daily reset should run now.

    Args:
        last_run_time: Last time the daily reset ran

    Returns:
        True if daily reset should run
    """
    # Get current Shanghai time
    now_utc = datetime.now(timezone.utc)
    shanghai_now = now_utc + RESET_TIMEZONE_OFFSET

    # If never run, check if we're past midnight
    if last_run_time is None:
        return shanghai_now.hour == 0 and shanghai_now.minute < 5  # Run in first 5 minutes of day

    # Check if last run was before today's midnight
    today_shanghai_midnight = shanghai_now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_run_shanghai = last_run_time.replace(tzinfo=timezone.utc) + RESET_TIMEZONE_OFFSET

    return last_run_shanghai < today_shanghai_midnight and shanghai_now.hour == 0 and shanghai_now.minute < 5


def reset_api_key(session: Session, api_key: UnifiedAPIKey) -> bool:
    """
    Reset daily token usage for a single API key.

    Args:
        session: Database session
        api_key: UnifiedAPIKey record to reset

    Returns:
        True if key was recovered from DAILY_LIMIT_EXCEEDED, False otherwise
    """
    today = get_today_in_timezone()

    # Check if already reset today
    if api_key.last_reset_date == today and api_key.daily_tokens_used == 0:
        return False

    # Check if key needs recovery (was DAILY_LIMIT_EXCEEDED)
    needs_recovery = api_key.status == UnifiedAPIKeyStatus.DAILY_LIMIT_EXCEEDED

    # Reset usage and date for all keys
    api_key.daily_tokens_used = 0
    api_key.last_reset_date = today

    if needs_recovery:
        # Recover key to ACTIVE status
        api_key.status = UnifiedAPIKeyStatus.ACTIVE

        # Create history entry
        create_limit_history_entry(
            session,
            unified_api_key_id=api_key.id,
            action="enable",
            tokens_used=0,
            token_limit=api_key.daily_token_limit or 0,
            reason="daily reset"
        )

        logger.info(
            f"Recovered API key {api_key.id} (user={api_key.user_id}) "
            f"from DAILY_LIMIT_EXCEEDED to ACTIVE"
        )
        return True

    return False


def run_daily_reset(session: Session) -> int:
    """
    Run daily reset for all API keys.

    Args:
        session: Database session

    Returns:
        Number of keys that were recovered from DAILY_LIMIT_EXCEEDED
    """
    # Get all active API keys (excluding REVOKED keys)
    statement = select(UnifiedAPIKey).where(
        UnifiedAPIKey.status != UnifiedAPIKeyStatus.REVOKED
    )
    all_keys = session.exec(statement).all()

    if not all_keys:
        logger.debug("No API keys to reset")
        return 0

    reset_count = 0
    recovered_count = 0
    for api_key in all_keys:
        try:
            if reset_api_key(session, api_key):
                recovered_count += 1
            reset_count += 1
        except Exception as e:
            logger.error(f"Error resetting API key {api_key.id}: {e}", exc_info=True)

    if reset_count > 0:
        session.commit()
        if recovered_count > 0:
            logger.info(f"Daily reset complete: reset {reset_count} API key(s), recovered {recovered_count} from DAILY_LIMIT_EXCEEDED")
        else:
            logger.info(f"Daily reset complete: reset {reset_count} API key(s)")

    return recovered_count


def main():
    """Main consumer loop"""
    logger.info("Starting daily reset consumer...")

    # Setup signal handlers
    setup_signals()

    # Main processing loop
    logger.info(f"Consumer ready, polling every {POLL_INTERVAL} seconds...")
    next_run_time = get_shanghai_midnight_utc()
    logger.info(f"Next daily reset scheduled at: {next_run_time}")

    last_run_time = None
    total_recovered = 0

    try:
        while not shutdown_requested:
            now_utc = datetime.now(timezone.utc)

            # Check if it's time to run daily reset
            if should_run_daily_reset(last_run_time):
                logger.info("Running daily reset...")

                session = DBSession(engine)
                try:
                    recovered = run_daily_reset(session)
                    total_recovered += recovered
                    last_run_time = now_utc

                    # Schedule next reset
                    next_run_time = get_shanghai_midnight_utc()
                    logger.info(f"Next daily reset scheduled at: {next_run_time}")
                finally:
                    session.close()

            # Wait for next poll (or shutdown)
            start_time = time.time()
            while not shutdown_requested and (time.time() - start_time) < POLL_INTERVAL:
                time.sleep(1)

    except Exception as e:
        logger.error(f"Fatal error in consumer loop: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info(f"Consumer shutdown. Total recovered: {total_recovered}")


if __name__ == "__main__":
    main()