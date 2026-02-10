"""
APScheduler configuration for automated grant discovery.

Runs discovery tasks on a schedule (default: daily at 2 AM).
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from .config import settings
from .database import SessionLocal
from .services.discovery.discovery_service import run_discovery

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()


def run_scheduled_discovery():
    """
    Execute scheduled grant discovery run.

    This function is called by APScheduler on schedule.
    Creates its own database session and handles errors gracefully.
    """
    logger.info("Starting scheduled grant discovery...")

    db = SessionLocal()
    try:
        # Parse sources from config (comma-separated string)
        sources_str = settings.DISCOVERY_SOURCES.strip()
        sources = [s.strip() for s in sources_str.split(",")] if sources_str else None

        # Run discovery
        run = run_discovery(
            db=db,
            sources=sources,
            send_notification=True  # Always send notification for scheduled runs
        )

        logger.info(
            f"Scheduled discovery completed: {run.grants_discovered} discovered, "
            f"{run.duplicates_found} duplicates, {run.errors} errors"
        )

    except Exception as e:
        logger.error(f"Scheduled discovery failed: {e}", exc_info=True)

    finally:
        db.close()


def job_listener(event):
    """
    Listen to job execution events for logging and monitoring.
    """
    if event.exception:
        logger.error(f"Job {event.job_id} failed: {event.exception}")
    else:
        logger.info(f"Job {event.job_id} executed successfully")


def start_scheduler():
    """
    Initialize and start the APScheduler.

    Registers the discovery job based on configuration settings.
    Should be called on application startup.
    """
    if not settings.DISCOVERY_ENABLED:
        logger.info("Discovery scheduler is disabled (DISCOVERY_ENABLED=False)")
        return

    # Parse cron schedule from config
    # Format: "minute hour day month weekday"
    # Example: "0 2 * * *" = Daily at 2:00 AM
    try:
        cron_parts = settings.DISCOVERY_SCHEDULE_CRON.split()
        if len(cron_parts) != 5:
            raise ValueError(f"Invalid cron format: {settings.DISCOVERY_SCHEDULE_CRON}")

        minute, hour, day, month, day_of_week = cron_parts

        # Create cron trigger
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week
        )

        # Add job to scheduler
        scheduler.add_job(
            func=run_scheduled_discovery,
            trigger=trigger,
            id="daily_grant_discovery",
            name="Automated Grant Discovery",
            replace_existing=True,
            misfire_grace_time=3600,  # Allow 1 hour grace for missed runs
        )

        # Add event listener
        scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        # Start scheduler
        scheduler.start()

        logger.info(
            f"Discovery scheduler started: {settings.DISCOVERY_SCHEDULE_CRON} "
            f"(sources: {settings.DISCOVERY_SOURCES})"
        )

    except Exception as e:
        logger.error(f"Failed to start discovery scheduler: {e}", exc_info=True)


def shutdown_scheduler():
    """
    Gracefully shutdown the scheduler.

    Should be called on application shutdown.
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Discovery scheduler shut down")


def trigger_immediate_discovery():
    """
    Trigger an immediate discovery run (outside of schedule).

    Useful for testing or manual triggers via API.
    Returns the job instance.
    """
    if not scheduler.running:
        logger.warning("Scheduler not running, cannot trigger immediate discovery")
        return None

    job = scheduler.add_job(
        func=run_scheduled_discovery,
        id=f"manual_discovery_{int(datetime.now().timestamp())}",
        name="Manual Grant Discovery",
        replace_existing=False
    )

    logger.info(f"Triggered immediate discovery job: {job.id}")
    return job


# For debugging: list scheduled jobs
def list_scheduled_jobs():
    """
    Get list of currently scheduled jobs.

    Returns list of job dictionaries with id, name, next_run_time.
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    return jobs
