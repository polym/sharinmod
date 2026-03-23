#!/usr/bin/env python3
"""
Claw Status Consumer

Standalone process that polls K8s Pod status and syncs to database.
Updates Claw.status based on Pod ready state:
- Pod ready → RUNNING
- Pod not ready & not timeout → PENDING
- Pod failed or timeout → FAILED

Run with: python -m api.consumers.claw_status_consumer

Graceful shutdown: SIGTERM or SIGINT (Ctrl+C)
"""
import os
import signal
import sys
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlmodel import Session, select

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.database import Session as DBSession, engine
from api.models.claw import Claw, ClawStatus
from api.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Polling interval in seconds
POLL_INTERVAL = 30

# Timeout for a claw to become ready (5 minutes)
READY_TIMEOUT = timedelta(minutes=5)

# Grace period after creation before marking as FAILED (30 seconds)
CREATION_GRACE_PERIOD = timedelta(seconds=30)

# Global flag for graceful shutdown
shutdown_requested = False

# Singleton K8s API client
_k8s_core_v1_client = None
_k8s_api_configured = False


def _configure_k8s_api():
    """Configure K8s API once (singleton pattern)."""
    global _k8s_api_configured
    if _k8s_api_configured:
        return

    from kubernetes import config
    import os

    kubeconfig_path = os.getenv("KUBECONFIG_PATH", os.path.expanduser("~/.kube/config"))
    try:
        config.load_kube_config(config_file=kubeconfig_path)
        logger.info(f"Loaded kubeconfig from {kubeconfig_path}")
    except Exception:
        # Fall back to in-cluster config (when running inside a pod)
        logger.info("Falling back to in-cluster config")
        config.load_incluster_config()

    _k8s_api_configured = True


def signal_handler(signum, frame):
    """Handle SIGTERM and SIGINT for graceful shutdown"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


def setup_signals():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


def _get_k8s_client():
    """Get or create CoreV1Api client (singleton)."""
    from kubernetes import client

    global _k8s_core_v1_client
    if _k8s_core_v1_client is None:
        _configure_k8s_api()
        _k8s_core_v1_client = client.CoreV1Api()
    return _k8s_core_v1_client


def _get_pod_ready_status(namespace: str, pod_name: str) -> Optional[bool]:
    """
    Query K8s Pod ready status.

    Args:
        namespace: K8s namespace
        pod_name: Pod name (e.g., claw-123-0)

    Returns:
        True if pod is ready, False if not ready, None if pod not found
    """
    from kubernetes.client.rest import ApiException

    core_v1 = _get_k8s_client()
    try:
        pod = core_v1.read_namespaced_pod(pod_name, namespace=namespace)
        # Check if all containers are ready
        if pod.status.container_statuses:
            return all(cs.ready for cs in pod.status.container_statuses)
        return False
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"Pod {pod_name} not found in namespace {namespace}")
            return None
        logger.error(f"Error querying pod {pod_name}: {e}")
        return None


def get_pending_and_running_claws(session: Session) -> List[Claw]:
    """Query all claws with PENDING or RUNNING status."""
    statement = select(Claw).where(Claw.status.in_([ClawStatus.PENDING, ClawStatus.RUNNING]))
    return session.exec(statement).all()


def sync_claw_status(session: Session, claw: Claw) -> bool:
    """
    Sync a single claw's status based on its Pod ready state.

    Args:
        session: Database session
        claw: Claw record to sync

    Returns:
        True if status was updated, False otherwise
    """
    if not claw.k8s_deployment_name:
        logger.warning(f"Claw {claw.id} has no k8s_deployment_name, skipping")
        return False

    namespace = claw.k8s_namespace or "default"
    pod_name = f"{claw.k8s_deployment_name}-0"

    pod_ready = _get_pod_ready_status(namespace, pod_name)

    if pod_ready is None:
        # Pod not found - check if still in creation grace period
        created_time = claw.created_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - created_time < CREATION_GRACE_PERIOD:
            # Still in grace period, don't mark as failed yet
            return False

        # Grace period passed - mark as FAILED
        if claw.status != ClawStatus.FAILED:
            logger.warning(f"Pod for claw {claw.id} not found after grace period, marking as FAILED")
            claw.status = ClawStatus.FAILED
            claw.updated_at = datetime.now(timezone.utc)
            session.add(claw)
            return True
        return False

    if pod_ready:
        # Pod is ready - mark as RUNNING
        if claw.status != ClawStatus.RUNNING:
            logger.info(f"Claw {claw.id} ({claw.name}) pod is ready, marking as RUNNING")
            claw.status = ClawStatus.RUNNING
            claw.updated_at = datetime.now(timezone.utc)
            session.add(claw)
            return True
        return False

    # Pod is not ready - check timeout
    created_time = claw.created_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - created_time > READY_TIMEOUT:
        # Timeout exceeded - mark as FAILED
        if claw.status != ClawStatus.FAILED:
            logger.warning(f"Claw {claw.id} ({claw.name}) timeout ({READY_TIMEOUT}), marking as FAILED")
            claw.status = ClawStatus.FAILED
            claw.updated_at = datetime.now(timezone.utc)
            session.add(claw)
            return True
        return False

    # Still within timeout - keep PENDING
    if claw.status != ClawStatus.PENDING:
        logger.info(f"Claw {claw.id} ({claw.name}) pod not ready, marking as PENDING")
        claw.status = ClawStatus.PENDING
        claw.updated_at = datetime.now(timezone.utc)
        session.add(claw)
        return True

    return False


def sync_all_claws(session: Session) -> int:
    """
    Sync all PENDING and RUNNING claws.

    Args:
        session: Database session

    Returns:
        Number of claws whose status was updated
    """
    claws = get_pending_and_running_claws(session)
    if not claws:
        return 0

    updated_count = 0
    for claw in claws:
        try:
            if sync_claw_status(session, claw):
                updated_count += 1
        except Exception as e:
            logger.error(f"Error syncing claw {claw.id}: {e}", exc_info=True)

    if updated_count > 0:
        session.commit()
        logger.info(f"Synced {updated_count} claw(s)")

    return updated_count


def main():
    """Main consumer loop"""
    logger.info("Starting claw status consumer...")

    # Setup signal handlers
    setup_signals()

    # Main processing loop
    logger.info(f"Consumer ready, polling every {POLL_INTERVAL} seconds...")
    sync_count = 0

    try:
        while not shutdown_requested:
            # Create a new database session for each poll
            session = DBSession(engine)

            try:
                # Sync all claws
                count = sync_all_claws(session)
                sync_count += count
                if count > 0:
                    logger.info(f"Total synced: {sync_count}")
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
        logger.info(f"Consumer shutdown. Total synced: {sync_count}")


if __name__ == "__main__":
    main()