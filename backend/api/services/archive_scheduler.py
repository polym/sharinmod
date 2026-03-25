"""
Archive scheduler service for automatic claw backups.
Uses APScheduler BackgroundScheduler to schedule backup jobs.
"""
import logging
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

import yaml
from api.config import _get_config_path
from api.services import k8s_service
from api.database import get_db
from api.models.claw import ClawStatus

logger = logging.getLogger(__name__)


class ArchiveScheduler:
    """
    Scheduler for automatic claw archive backups.

    Supports two types of scheduled backups:
    - Daily: Cron-based backup (e.g., every day at 6:00 AM)
    - Interval: Periodic backup (e.g., every 20 minutes)
    """

    def __init__(self):
        self.scheduler: Optional[BackgroundScheduler] = None
        self.enabled = False
        self.config = {}

    def load_config(self) -> dict:
        """Load archive scheduler configuration from config.yaml."""
        try:
            config_path = _get_config_path()
            with open(config_path, "r", encoding="utf-8") as f:
                full_config = yaml.safe_load(f) or {}

            # Check if auto archive is enabled
            prunc_enabled = full_config.get("prunc_enabled", False) is True
            claws_archive_enabled = full_config.get("claws_archive_enabled", False) is True
            auto_enabled = full_config.get("claws_archive_auto_enabled", False) is True

            if not prunc_enabled or not claws_archive_enabled or not auto_enabled:
                return {
                    "enabled": False,
                }

            return {
                "enabled": True,
                "schedule_daily": full_config.get("claws_archive_schedule_daily", "0 6 * * *"),
                "schedule_interval": full_config.get("claws_archive_schedule_interval", 20),
                "retention_daily": full_config.get("claws_archive_retention_daily", 1),
                "retention_interval": full_config.get("claws_archive_retention_interval", 5),
            }
        except Exception as e:
            logger.error(f"Failed to load archive scheduler config: {e}")
            return {"enabled": False}

    def _daily_backup_job(self):
        """Execute daily backup job for all running claws."""
        logger.info("Starting daily archive backup job")
        db = next(get_db())

        try:
            # Get all claws with RUNNING status
            from sqlmodel import select
            from api.models.claw import Claw

            statement = select(Claw).where(Claw.status == ClawStatus.RUNNING)
            result = db.exec(statement).all()

            for claw in result:
                claw_id = claw.id
                namespace = claw.k8s_namespace or "default"

                try:
                    # Clean up old daily archives first (keep only retention count)
                    k8s_service.cleanup_old_archives(
                        claw_id,
                        namespace,
                        retention_config={
                            "daily_retention": self.config.get("retention_daily", 1),
                            "interval_retention": self.config.get("retention_interval", 5),
                        },
                    )

                    # Create new daily archive
                    timestamp = k8s_service.create_auto_archive(
                        claw_id,
                        namespace,
                        schedule_type="daily",
                    )
                    if timestamp:
                        logger.info(f"Created daily archive for claw-{claw_id}: {timestamp}")
                    else:
                        logger.warning(f"Failed to create daily archive for claw-{claw_id}")
                except Exception as e:
                    logger.error(f"Error processing daily backup for claw-{claw_id}: {e}")
        except Exception as e:
            logger.error(f"Error in daily backup job: {e}")
        finally:
            db.close()

        logger.info("Completed daily archive backup job")

    def _interval_backup_job(self):
        """Execute interval backup job for all running claws."""
        logger.info("Starting interval archive backup job")
        db = next(get_db())

        try:
            # Get all claws with RUNNING status
            from sqlmodel import select
            from api.models.claw import Claw

            statement = select(Claw).where(Claw.status == ClawStatus.RUNNING)
            result = db.exec(statement).all()

            for claw in result:
                claw_id = claw.id
                namespace = claw.k8s_namespace or "default"

                try:
                    # Create new interval archive
                    timestamp = k8s_service.create_auto_archive(
                        claw_id,
                        namespace,
                        schedule_type="interval",
                    )
                    if timestamp:
                        logger.info(f"Created interval archive for claw-{claw_id}: {timestamp}")
                    else:
                        logger.warning(f"Failed to create interval archive for claw-{claw_id}")
                except Exception as e:
                    logger.error(f"Error processing interval backup for claw-{claw_id}: {e}")
        except Exception as e:
            logger.error(f"Error in interval backup job: {e}")
        finally:
            db.close()

        logger.info("Completed interval archive backup job")

    def start(self):
        """Start the archive scheduler."""
        self.config = self.load_config()

        if not self.config.get("enabled"):
            logger.info("Archive auto-backup is disabled, scheduler not started")
            return

        if self.scheduler and self.scheduler.running:
            logger.warning("Archive scheduler is already running")
            return

        try:
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()

            # Add daily cron job
            daily_cron = self.config.get("schedule_daily", "0 6 * * *")
            self.scheduler.add_job(
                self._daily_backup_job,
                CronTrigger.from_crontab(daily_cron),
                id="daily_archive_backup",
                name="Daily Archive Backup",
                replace_existing=True,
            )
            logger.info(f"Scheduled daily archive backup: {daily_cron}")

            # Add interval job
            interval_minutes = self.config.get("schedule_interval", 20)
            self.scheduler.add_job(
                self._interval_backup_job,
                IntervalTrigger(minutes=interval_minutes),
                id="interval_archive_backup",
                name="Interval Archive Backup",
                replace_existing=True,
            )
            logger.info(f"Scheduled interval archive backup: every {interval_minutes} minutes")

            self.enabled = True
            logger.info("Archive scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start archive scheduler: {e}")
            if self.scheduler:
                self.scheduler.shutdown()
            self.scheduler = None
            self.enabled = False

    def shutdown(self):
        """Shutdown the archive scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Archive scheduler shutdown complete")
        self.scheduler = None
        self.enabled = False

    def get_next_run_time(self, job_id: str) -> Optional[str]:
        """Get the next scheduled run time for a job."""
        if not self.scheduler or not self.scheduler.running:
            return None

        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return None


# Global scheduler instance
archive_scheduler = ArchiveScheduler()
