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
from .models.grants_db import Grant

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


def refresh_grant_statuses():
    """Weekly job: auto-update grant statuses based on deadline proximity."""
    from datetime import date as date_cls
    logger.info("Running weekly grant status refresh...")
    db = SessionLocal()
    try:
        grants = db.query(Grant).all()
        today = date_cls.today()
        updated = 0
        for grant in grants:
            if not grant.deadline or grant.deadline in ("rolling", "annual"):
                continue
            try:
                dl = date_cls.fromisoformat(grant.deadline)
            except (ValueError, TypeError):
                continue
            days_left = (dl - today).days
            if days_left < 0:
                new_status = "closed"
            elif days_left <= 30:
                new_status = "closing_soon"
            else:
                new_status = "open"
            if new_status != grant.status:
                grant.status = new_status
                updated += 1
        db.commit()
        logger.info("Grant status refresh complete: %d grant(s) updated", updated)
    except Exception:
        logger.exception("Grant status refresh failed")
        db.rollback()
    finally:
        db.close()


def send_deadline_alerts():
    """Daily job: email applicants 30, 7, and 1 day(s) before a grant deadline."""
    import json
    from datetime import date as date_cls
    from .services.email import send_email, is_email_available, _base_template

    if not is_email_available():
        logger.info("Email not configured — skipping deadline alerts")
        return

    logger.info("Running daily deadline alert job...")
    db = SessionLocal()
    try:
        from .models.grants_db import GrantApplication
        today = date_cls.today()
        thresholds = [30, 7, 1]
        sent_count = 0

        apps = db.query(GrantApplication).filter(
            GrantApplication.applicant_email.isnot(None)
        ).all()

        for app in apps:
            grant = app.grant
            if not grant or not grant.deadline or grant.deadline in ("rolling", "annual"):
                continue
            if grant.status == "closed":
                continue
            try:
                dl = date_cls.fromisoformat(grant.deadline)
            except (ValueError, TypeError):
                continue

            days_left = (dl - today).days
            if days_left < 0:
                continue

            try:
                already_sent = json.loads(app.deadline_alerts_sent or "[]")
            except (ValueError, TypeError):
                already_sent = []

            for threshold in thresholds:
                if days_left <= threshold and threshold not in already_sent:
                    urgency = "TODAY" if days_left == 0 else f"{days_left} day{'s' if days_left != 1 else ''}"
                    color = "#dc2626" if days_left <= 7 else "#d97706"
                    subject = f"⏰ {grant.grant_name} closes in {urgency} — SyrHousing"
                    html = _base_template(f"""
                        <h2 style="color:#1a2744;margin-top:0">Grant Deadline Reminder</h2>
                        <p>Hi {app.applicant_name or 'there'},</p>
                        <p>You expressed interest in <strong>{grant.grant_name}</strong>.
                        The application deadline is coming up soon:</p>
                        <div style="text-align:center;margin:20px 0">
                            <div style="display:inline-block;background:{color};color:#fff;
                                padding:12px 28px;border-radius:8px;font-size:20px;font-weight:800">
                                {urgency} left
                            </div>
                        </div>
                        <table style="width:100%;border-collapse:collapse;font-size:14px;margin:16px 0">
                            <tr style="background:#f8fafc">
                                <td style="padding:8px 12px;font-weight:bold;width:140px">Deadline</td>
                                <td style="padding:8px 12px">{grant.deadline}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px 12px;font-weight:bold">Funding</td>
                                <td style="padding:8px 12px">${grant.amount_min:,.0f} – {'${:,.0f}'.format(grant.amount_max) if grant.amount_max else 'varies'}</td>
                            </tr>
                            {'<tr style="background:#f8fafc"><td style="padding:8px 12px;font-weight:bold">Phone</td><td style="padding:8px 12px">' + grant.agency_phone + '</td></tr>' if grant.agency_phone else ''}
                            {'<tr><td style="padding:8px 12px;font-weight:bold">Email</td><td style="padding:8px 12px">' + grant.agency_email + '</td></tr>' if grant.agency_email else ''}
                        </table>
                        {('<div style="text-align:center;margin:20px 0"><a href="' + grant.application_url + '" style="background:#0d9488;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px">Apply Now →</a></div>') if grant.application_url else ''}
                        <p style="color:#6b7280;font-size:13px">
                            Need help? Call <strong>211</strong> or contact the agency directly.
                        </p>
                    """)
                    if send_email(app.applicant_email, subject, html):
                        already_sent.append(threshold)
                        app.deadline_alerts_sent = json.dumps(already_sent)
                        sent_count += 1

        db.commit()
        logger.info("Deadline alerts complete: %d sent", sent_count)
    except Exception:
        logger.exception("Deadline alert job failed")
        db.rollback()
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

        # Daily deadline alerts — every day at 8 AM
        scheduler.add_job(
            func=send_deadline_alerts,
            trigger=CronTrigger(hour=8, minute=0),
            id="daily_deadline_alerts",
            name="Daily Deadline Alerts",
            replace_existing=True,
            misfire_grace_time=3600,
        )

        # Weekly grant status refresh — every Monday at 3 AM
        scheduler.add_job(
            func=refresh_grant_statuses,
            trigger=CronTrigger(day_of_week="mon", hour=3, minute=0),
            id="weekly_status_refresh",
            name="Weekly Grant Status Refresh",
            replace_existing=True,
            misfire_grace_time=3600,
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
