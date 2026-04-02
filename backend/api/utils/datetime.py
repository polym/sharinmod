"""
Datetime utilities for timezone-aware operations

This module provides centralized timezone handling functions to ensure
consistent date/time calculations across the application.
"""
from datetime import datetime, date, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Asia/Shanghai"
UTC8_OFFSET = timedelta(hours=8)


def get_timezone_offset(tz_str: Optional[str] = None) -> timedelta:
    """
    Get timezone offset for a given timezone string

    Args:
        tz_str: Timezone string (e.g., "Asia/Shanghai", "UTC")
                 Defaults to DEFAULT_TIMEZONE

    Returns:
        Timedelta offset from UTC
    """
    if not tz_str:
        tz_str = DEFAULT_TIMEZONE

    try:
        tz = ZoneInfo(tz_str)
        # Get current offset for this timezone
        now = datetime.now(tz)
        return now.utcoffset() or UTC8_OFFSET
    except Exception:
        return UTC8_OFFSET


def get_today_in_timezone(tz_str: Optional[str] = None) -> date:
    """
    Get current date in specified timezone

    Args:
        tz_str: Timezone string (e.g., "Asia/Shanghai", "UTC")
                 Defaults to DEFAULT_TIMEZONE

    Returns:
        Current date in the specified timezone
    """
    if not tz_str:
        tz_str = DEFAULT_TIMEZONE

    try:
        tz = ZoneInfo(tz_str)
        return datetime.now(tz).date()
    except Exception:
        return (datetime.now(timezone.utc) + UTC8_OFFSET).date()
