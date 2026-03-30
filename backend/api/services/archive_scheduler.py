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
            logger.info(f"[ArchiveScheduler] Loading config from: {config_path}")

            with open(config_path, "r", encoding="utf-8") as f:
                full_config = yaml.safe_load(f) or {}

            # Log raw config values for debugging
            prunc_raw = full_config.get("prunc_enabled")
            claws_archive_raw = full_config.get("claws_archive_enabled")
            auto_raw = full_config.get("claws_archive_auto_enabled")

            logger.info(f"[ArchiveScheduler] Raw config values: prunc_enabled={prunc_raw!r} (type: {type(prunc_raw).__name__}), "
                       f"claws_archive_enabled={claws_archive_raw!r} (type: {type(claws_archive_raw).__name__}), "
                       f"claws_archive_auto_enabled={auto_raw!r} (type: {type(auto_raw).__name__})")

            # Check if auto archive is enabled
            # Handle both bool and string "true"/"false" from YAML
            prunc_enabled = self._to_bool(prunc_raw)
            claws_archive_enabled = self._to_bool(claws_archive_raw)
            auto_enabled = self._to_bool(auto_raw)

            logger.info(f"[ArchiveScheduler] Parsed config values: prunc_enabled={prunc_enabled}, "
                       f"claws_archive_enabled={claws_archive_enabled}, auto_enabled={auto_enabled}")

            if not prunc_enabled:
                logger.info("[ArchiveScheduler] Auto archive disabled: prunc_enabled is False")
                return {"enabled": False}
            if not claws_archive_enabled:
                logger.info("[ArchiveScheduler] Auto archive disabled: claws_archive_enabled is False")
                return {"enabled": False}
            if not auto_enabled:
                logger.info("[ArchiveScheduler] Auto archive disabled: claws_archive_auto_enabled is False")
                return {"enabled": False}

            config = {
                "enabled": True,
                "schedule_daily": full_config.get("claws_archive_schedule_daily", "0 6 * * *"),
                "schedule_interval": full_config.get("claws_archive_schedule_interval", 20),
                "retention_daily": full_config.get("claws_archive_retention_daily", 1),
                "retention_interval": full_config.get("claws_archive_retention_interval", 5),
            }
            logger.info(f"[ArchiveScheduler] Auto archive config loaded: {config}")
            return config
        except Exception as e:
            logger.error(f"[ArchiveScheduler] Failed to load config: {e}", exc_info=True)
            return {"enabled": False}

    def _to_bool(self, value) -> bool:
        """Convert various types to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def _daily_backup_job(self):
        """Execute daily backup job for all running claws."""
        logger.info("[ArchiveScheduler][DailyBackup] ===== STARTING DAILY BACKUP JOB =====")
        db = next(get_db())

        try:
            # Get all claws with RUNNING status
            from sqlmodel import select
            from api.models.claw import Claw

            statement = select(Claw).where(Claw.status == ClawStatus.RUNNING)
            result = db.exec(statement).all()
            logger.info(f"[ArchiveScheduler][DailyBackup] Found {len(result)} RUNNING claws to backup")

            for claw in result:
                claw_id = claw.id
                namespace = claw.k8s_namespace or "default"
                logger.info(f"[ArchiveScheduler][DailyBackup] Processing claw-{claw_id} (namespace: {namespace})")

                try:
                    # Clean up old daily archives first (keep only retention count)
                    logger.debug(f"[ArchiveScheduler][DailyBackup] claw-{claw_id}: Cleaning up old archives...")
                    k8s_service.cleanup_old_archives(
                        claw_id,
                        namespace,
                        retention_config={
                            "daily_retention": self.config.get("retention_daily", 1),
                            "interval_retention": self.config.get("retention_interval", 5),
                        },
                    )

                    # Create new daily archive
                    logger.debug(f"[ArchiveScheduler][DailyBackup] claw-{claw_id}: Creating daily archive...")
                    timestamp = k8s_service.create_auto_archive(
                        claw_id,
                        namespace,
                        schedule_type="daily",
                    )
                    if timestamp:
                        logger.info(f"[ArchiveScheduler][DailyBackup] claw-{claw_id}: Created daily archive with timestamp {timestamp}")
                    else:
                        logger.error(f"[ArchiveScheduler][DailyBackup] claw-{claw_id}: Failed to create daily archive")
                except Exception as e:
                    logger.error(f"[ArchiveScheduler][DailyBackup] claw-{claw_id}: Error - {e}", exc_info=True)
        except Exception as e:
            logger.error(f"[ArchiveScheduler][DailyBackup] Error in daily backup job: {e}", exc_info=True)
        finally:
            db.close()

        logger.info("[ArchiveScheduler][DailyBackup] ===== DAILY BACKUP JOB COMPLETED =====")

    def _interval_backup_job(self):
        """Execute interval backup job for all running claws."""
        logger.info("[ArchiveScheduler][IntervalBackup] ===== STARTING INTERVAL BACKUP JOB =====")
        db = next(get_db())

        try:
            # Get all claws with RUNNING status
            from sqlmodel import select
            from api.models.claw import Claw

            statement = select(Claw).where(Claw.status == ClawStatus.RUNNING)
            result = db.exec(statement).all()
            logger.info(f"[ArchiveScheduler][IntervalBackup] Found {len(result)} RUNNING claws to backup")

            for claw in result:
                claw_id = claw.id
                namespace = claw.k8s_namespace or "default"
                logger.info(f"[ArchiveScheduler][IntervalBackup] Processing claw-{claw_id} (namespace: {namespace})")

                try:
                    # Clean up old interval archives first (keep only retention count)
                    retention_interval = self.config.get("retention_interval", 5)
                    if retention_interval is not None and retention_interval < 1:
                        logger.warning(f"[ArchiveScheduler][IntervalBackup] claw-{claw_id}: Invalid retention_interval={retention_interval}, using default 5")
                        retention_interval = 5
                    logger.info(f"[ArchiveScheduler][IntervalBackup] claw-{claw_id}: Cleaning up old interval archives (retention={retention_interval})...")
                    k8s_service.cleanup_old_archives(
                        claw_id,
                        namespace,
                        retention_config={
                            "interval_retention": retention_interval,
                        },
                    )

                    # Create new interval archive
                    logger.debug(f"[ArchiveScheduler][IntervalBackup] claw-{claw_id}: Creating interval archive...")
                    timestamp = k8s_service.create_auto_archive(
                        claw_id,
                        namespace,
                        schedule_type="interval",
                    )
                    if timestamp:
                        logger.info(f"[ArchiveScheduler][IntervalBackup] claw-{claw_id}: Created interval archive with timestamp {timestamp}")
                    else:
                        logger.error(f"[ArchiveScheduler][IntervalBackup] claw-{claw_id}: Failed to create interval archive")
                except Exception as e:
                    logger.error(f"[ArchiveScheduler][IntervalBackup] claw-{claw_id}: Error - {e}", exc_info=True)
        except Exception as e:
            logger.error(f"[ArchiveScheduler][IntervalBackup] Error in interval backup job: {e}", exc_info=True)
        finally:
            db.close()

        logger.info("[ArchiveScheduler][IntervalBackup] ===== INTERVAL BACKUP JOB COMPLETED =====")

    def start(self):
        """Start the archive scheduler."""
        logger.info("[ArchiveScheduler] ===== STARTING SCHEDULER =====")
        self.config = self.load_config()

        if not self.config.get("enabled"):
            logger.warning("[ArchiveScheduler] Archive auto-backup is disabled, scheduler not started")
            return

        if self.scheduler and self.scheduler.running:
            logger.warning("[ArchiveScheduler] Archive scheduler is already running")
            return

        try:
            logger.info("[ArchiveScheduler] Creating BackgroundScheduler...")
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
            logger.info("[ArchiveScheduler] BackgroundScheduler started")

            # Add daily cron job
            daily_cron = self.config.get("schedule_daily", "0 6 * * *")
            logger.info(f"[ArchiveScheduler] Adding daily cron job: {daily_cron}")
            self.scheduler.add_job(
                self._daily_backup_job,
                CronTrigger.from_crontab(daily_cron),
                id="daily_archive_backup",
                name="Daily Archive Backup",
                replace_existing=True,
            )
            logger.info(f"[ArchiveScheduler] Scheduled daily archive backup: {daily_cron}")

            # Add interval job
            interval_minutes = self.config.get("schedule_interval", 20)
            logger.info(f"[ArchiveScheduler] Adding interval job: every {interval_minutes} minutes")
            self.scheduler.add_job(
                self._interval_backup_job,
                IntervalTrigger(minutes=interval_minutes),
                id="interval_archive_backup",
                name="Interval Archive Backup",
                replace_existing=True,
            )
            logger.info(f"[ArchiveScheduler] Scheduled interval archive backup: every {interval_minutes} minutes")

            self.enabled = True
            logger.info("[ArchiveScheduler] ===== SCHEDULER STARTED SUCCESSFULLY =====")
            logger.info(f"[ArchiveScheduler] Scheduler running: {self.scheduler.running}")
            logger.info(f"[ArchiveScheduler] Number of jobs: {len(self.scheduler.get_jobs())}")
            for job in self.scheduler.get_jobs():
                logger.info(f"[ArchiveScheduler] Job: id={job.id}, name={job.name}, next_run_time={job.next_run_time}")
        except Exception as e:
            logger.error(f"[ArchiveScheduler] Failed to start scheduler: {e}", exc_info=True)
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
