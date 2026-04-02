"""
Archive config service for managing claw archive backup configuration.
Provides functions to read and write archive config from config.yaml.
"""
import logging
import os
import tempfile
from typing import Dict, Any

import yaml
from apscheduler.triggers.cron import CronTrigger

from api.config import _get_config_path

logger = logging.getLogger(__name__)


def get_archive_config() -> Dict[str, Any]:
    """Get archive configuration from config.yaml.

    Returns:
        Dict[str, Any]: Archive configuration containing:
            - claws_archive_enabled: bool
            - claws_archive_auto_enabled: bool
            - claws_archive_schedule_daily: str
            - claws_archive_schedule_interval: int
            - claws_archive_retention_daily: int
            - claws_archive_retention_interval: int
            - claws_archive_max_manual: int

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config file is malformed.
    """
    try:
        config_path = _get_config_path()

        with open(config_path, "r", encoding="utf-8") as f:
            full_config = yaml.safe_load(f) or {}

        return {
            "claws_archive_enabled": _to_bool(full_config.get("claws_archive_enabled", True)),
            "claws_archive_auto_enabled": _to_bool(full_config.get("claws_archive_auto_enabled", True)),
            "claws_archive_schedule_daily": full_config.get("claws_archive_schedule_daily", "0 6 * * *"),
            "claws_archive_schedule_interval": full_config.get("claws_archive_schedule_interval", 20),
            "claws_archive_retention_daily": full_config.get("claws_archive_retention_daily", 1),
            "claws_archive_retention_interval": full_config.get("claws_archive_retention_interval", 5),
            "claws_archive_max_manual": full_config.get("claws_archive_max_manual", 5),
        }
    except FileNotFoundError:
        logger.error(f"[ArchiveConfig] Configuration file not found: {config_path}")
        raise
    except Exception as e:
        logger.error(f"[ArchiveConfig] Failed to load archive config: {e}")
        raise ValueError(f"Failed to load archive config: {e}")


def update_archive_config(
    claws_archive_enabled: bool,
    claws_archive_auto_enabled: bool,
    claws_archive_schedule_daily: str,
    claws_archive_schedule_interval: int,
    claws_archive_retention_daily: int,
    claws_archive_retention_interval: int,
    claws_archive_max_manual: int,
) -> Dict[str, Any]:
    """Update archive configuration in config.yaml.

    Args:
        claws_archive_enabled: Backup feature master switch
        claws_archive_auto_enabled: Auto backup switch
        claws_archive_schedule_daily: Daily backup cron expression
        claws_archive_schedule_interval: Interval backup minutes
        claws_archive_retention_daily: Daily backup retention count
        claws_archive_retention_interval: Interval backup retention count
        claws_archive_max_manual: Maximum manual backups

    Returns:
        Dict[str, Any]: Updated archive configuration

    Raises:
        ValueError: If cron expression is invalid or config update fails.
        FileNotFoundError: If config file doesn't exist.

    """
    # Validate cron expression
    try:
        CronTrigger.from_crontab(claws_archive_schedule_daily)
    except Exception as e:
        logger.error(f"[ArchiveConfig] Invalid cron expression: {claws_archive_schedule_daily} - {e}")
        raise ValueError(f"Invalid cron expression: {e}")

    try:
        config_path = _get_config_path()

        # Load existing config
        with open(config_path, "r", encoding="utf-8") as f:
            full_config = yaml.safe_load(f) or {}

        # Update archive config fields
        full_config["claws_archive_enabled"] = claws_archive_enabled
        full_config["claws_archive_auto_enabled"] = claws_archive_auto_enabled
        full_config["claws_archive_schedule_daily"] = claws_archive_schedule_daily
        full_config["claws_archive_schedule_interval"] = claws_archive_schedule_interval
        full_config["claws_archive_retention_daily"] = claws_archive_retention_daily
        full_config["claws_archive_retention_interval"] = claws_archive_retention_interval
        full_config["claws_archive_max_manual"] = claws_archive_max_manual

        # Write to temporary file first, then atomic rename
        dir_name = os.path.dirname(config_path)
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".tmp",
            dir=dir_name,
            encoding="utf-8",
            delete=False,
        ) as tmp_file:
            yaml.dump(full_config, tmp_file, allow_unicode=True, default_flow_style=False)
            tmp_path = tmp_file.name

        # Atomic rename to replace original config
        os.replace(tmp_path, config_path)

        logger.info(f"[ArchiveConfig] Archive config updated successfully: {config_path}")

        return {
            "claws_archive_enabled": claws_archive_enabled,
            "claws_archive_auto_enabled": claws_archive_auto_enabled,
            "claws_archive_schedule_daily": claws_archive_schedule_daily,
            "claws_archive_schedule_interval": claws_archive_schedule_interval,
            "claws_archive_retention_daily": claws_archive_retention_daily,
            "claws_archive_retention_interval": claws_archive_retention_interval,
            "claws_archive_max_manual": claws_archive_max_manual,
        }
    except FileNotFoundError:
        logger.error(f"[ArchiveConfig] Configuration file not found: {config_path}")
        raise
    except Exception as e:
        logger.error(f"[ArchiveConfig] Failed to update archive config: {e}")
        raise ValueError(f"Failed to update archive config: {e}")


def _to_bool(value) -> bool:
    """Convert various types to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)
