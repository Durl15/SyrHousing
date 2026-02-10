"""
Notifications API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from ..database import get_db
from ..services.notifications import (
    get_grants_closing_soon,
    get_new_grants,
    get_recent_deadline_changes,
    run_daily_notifications,
    send_custom_alert,
)
from ..auth import get_current_user, require_admin
from ..models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


class CustomAlertRequest(BaseModel):
    subject: str
    message: str
    user_emails: Optional[List[str]] = None


@router.get("/closing-soon")
def get_closing_soon_grants(
    db: Session = Depends(get_db),
    days: int = 30,
    current_user: User = Depends(get_current_user),
):
    """
    Get list of grants with deadlines within specified days.
    """
    try:
        closing_soon = get_grants_closing_soon(db, days_threshold=days)

        return {
            "count": len(closing_soon),
            "grants": [
                {
                    "program_key": item["program"].program_key,
                    "name": item["program"].name,
                    "deadline": item["program"].status_or_deadline,
                    "deadline_date": item["deadline_date"].isoformat() if item["deadline_date"] else None,
                    "days_remaining": item["days_remaining"],
                    "agency": item["program"].agency,
                    "phone": item["program"].phone,
                    "website": item["program"].website,
                }
                for item in closing_soon
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get closing soon grants: {str(e)}")


@router.get("/new-grants")
def get_new_grants_list(
    db: Session = Depends(get_db),
    hours: int = 24,
    current_user: User = Depends(get_current_user),
):
    """
    Get list of grants added within specified hours.
    """
    try:
        new_grants = get_new_grants(db, hours_threshold=hours)

        return {
            "count": len(new_grants),
            "grants": [
                {
                    "program_key": program.program_key,
                    "name": program.name,
                    "max_benefit": program.max_benefit,
                    "agency": program.agency,
                    "phone": program.phone,
                    "status_or_deadline": program.status_or_deadline,
                    "created_at": program.created_at.isoformat(),
                }
                for program in new_grants
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get new grants: {str(e)}")


@router.get("/deadline-changes")
def get_deadline_changes_list(
    db: Session = Depends(get_db),
    hours: int = 24,
    current_user: User = Depends(get_current_user),
):
    """
    Get list of grants with recent status/deadline changes.
    """
    try:
        changes = get_recent_deadline_changes(db, hours_threshold=hours)

        return {
            "count": len(changes),
            "changes": [
                {
                    "program_key": item["program"].program_key,
                    "name": item["program"].name,
                    "current_status": item["current_status"],
                    "deadline": item["program"].status_or_deadline,
                    "agency": item["program"].agency,
                    "phone": item["program"].phone,
                    "changed_at": item["scan_result"].timestamp.isoformat(),
                }
                for item in changes
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deadline changes: {str(e)}")


@router.post("/run-daily-check")
def run_daily_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Manually trigger daily notification check.
    Admin only. Usually run by scheduled task.
    """
    try:
        stats = run_daily_notifications(db)
        return {
            "message": "Daily notifications completed",
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run daily notifications: {str(e)}")


@router.post("/send-custom-alert")
def send_custom_alert_endpoint(
    request: CustomAlertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Send custom alert to users.
    Admin only.
    """
    try:
        sent_count = send_custom_alert(
            db,
            subject=request.subject,
            message=request.message,
            user_emails=request.user_emails,
        )

        return {
            "message": "Custom alert sent",
            "emails_sent": sent_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send custom alert: {str(e)}")


@router.get("/summary")
def get_notification_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get summary of all notification-worthy events.
    """
    try:
        closing_soon = get_grants_closing_soon(db, days_threshold=30)
        new_grants = get_new_grants(db, hours_threshold=24)
        deadline_changes = get_recent_deadline_changes(db, hours_threshold=24)

        # Count urgent (7 days or less)
        urgent_count = sum(1 for item in closing_soon if item['days_remaining'] <= 7)

        return {
            "closing_soon": {
                "total": len(closing_soon),
                "urgent": urgent_count,
            },
            "new_grants": len(new_grants),
            "deadline_changes": len(deadline_changes),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification summary: {str(e)}")
