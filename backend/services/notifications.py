"""
Email notification service for grant deadline alerts and updates.
Monitors grant deadlines and sends email notifications for:
- Grants closing within 30 days
- New grants becoming available
- Deadline changes detected by scanner
"""

import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..config import settings
from ..models.program import Program
from ..models.user import User
from ..models.scan import ScanResult, ScanState
from ..models.discovered_grant import DiscoveredGrant, DiscoveryRun
from .email import send_email


def parse_deadline_date(deadline_text: str) -> Optional[datetime]:
    """
    Parse deadline text to extract a datetime object.
    Returns None if no valid date found.
    """
    if not deadline_text:
        return None

    text = deadline_text.lower()

    # Date patterns to try
    patterns = [
        # MM/DD/YYYY
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: datetime(int(m[3]), int(m[1]), int(m[2]))),
        # YYYY-MM-DD
        (r'(\d{4})-(\d{2})-(\d{2})', lambda m: datetime(int(m[1]), int(m[2]), int(m[3]))),
        # Month Day, Year
        (r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})',
         lambda m: datetime(
             int(m[3]),
             ['january', 'february', 'march', 'april', 'may', 'june',
              'july', 'august', 'september', 'october', 'november', 'december'].index(m[1]) + 1,
             int(m[2])
         )),
    ]

    for pattern, converter in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return converter(match)
            except (ValueError, IndexError):
                continue

    return None


def get_grants_closing_soon(db: Session, days_threshold: int = 30) -> List[Dict]:
    """
    Get all grants that have deadlines within the specified number of days.
    Returns list of dicts with grant info and days remaining.
    """
    programs = db.query(Program).filter(Program.is_active == True).all()

    closing_soon = []
    now = datetime.now()

    for program in programs:
        if not program.status_or_deadline:
            continue

        deadline_date = parse_deadline_date(program.status_or_deadline)

        if deadline_date:
            days_remaining = (deadline_date - now).days

            if 0 <= days_remaining <= days_threshold:
                closing_soon.append({
                    'program': program,
                    'deadline_date': deadline_date,
                    'days_remaining': days_remaining,
                })

    # Sort by days remaining (most urgent first)
    closing_soon.sort(key=lambda x: x['days_remaining'])

    return closing_soon


def get_new_grants(db: Session, hours_threshold: int = 24) -> List[Program]:
    """
    Get grants that were added within the last N hours.
    """
    threshold_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)

    new_grants = db.query(Program).filter(
        and_(
            Program.is_active == True,
            Program.created_at >= threshold_time
        )
    ).all()

    return new_grants


def get_recent_deadline_changes(db: Session, hours_threshold: int = 24) -> List[Dict]:
    """
    Get programs that had deadline/status changes detected by scanner.
    """
    threshold_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)

    # Get recent scan results that showed changes
    recent_changes = db.query(ScanResult).filter(
        and_(
            ScanResult.timestamp >= threshold_time,
            ScanResult.changed == True,
        )
    ).all()

    changes_info = []

    for scan_result in recent_changes:
        # Get program details
        program = db.query(Program).filter(
            Program.program_key == scan_result.watchlist_program_key
        ).first()

        if program:
            # Get scan state for current status
            scan_state = db.query(ScanState).filter(
                ScanState.program_key == program.program_key
            ).first()

            changes_info.append({
                'program': program,
                'scan_result': scan_result,
                'current_status': scan_state.status if scan_state else 'unknown',
            })

    return changes_info


def send_closing_soon_alert(user_email: str, user_name: str, closing_grants: List[Dict]) -> bool:
    """
    Send email alert for grants closing soon.
    """
    if not closing_grants:
        return False

    # Build email body
    lines = [
        f"Hello {user_name},",
        "",
        f"The following grants have deadlines within the next 30 days:",
        "",
    ]

    for item in closing_grants:
        program = item['program']
        days = item['days_remaining']

        urgency = "🔴 URGENT" if days <= 7 else "⚠️ Soon"

        lines.append(f"{urgency} - {program.name}")
        lines.append(f"   Deadline: {program.status_or_deadline}")
        lines.append(f"   Days Remaining: {days}")

        if program.agency:
            lines.append(f"   Agency: {program.agency}")
        if program.phone:
            lines.append(f"   Phone: {program.phone}")
        if program.website:
            lines.append(f"   Website: {program.website}")

        lines.append("")

    lines.extend([
        "Don't miss out! Contact the agencies soon to confirm eligibility and apply.",
        "",
        "Best regards,",
        "SyrHousing Grant Agent",
        "",
        f"View all grants: {settings.FRONTEND_URL}/programs",
    ])

    subject = f"⏰ {len(closing_grants)} Grant Deadline(s) Coming Up!"
    body = "\n".join(lines)

    return send_email(user_email, subject, body)


def send_new_grants_alert(user_email: str, user_name: str, new_grants: List[Program]) -> bool:
    """
    Send email alert for new grants added to the database.
    """
    if not new_grants:
        return False

    lines = [
        f"Hello {user_name},",
        "",
        f"Great news! {len(new_grants)} new grant program(s) have been added:",
        "",
    ]

    for program in new_grants:
        lines.append(f"✨ {program.name}")

        if program.max_benefit:
            lines.append(f"   Benefit: {program.max_benefit}")
        if program.agency:
            lines.append(f"   Agency: {program.agency}")
        if program.phone:
            lines.append(f"   Phone: {program.phone}")
        if program.status_or_deadline:
            lines.append(f"   Status: {program.status_or_deadline}")

        lines.append("")

    lines.extend([
        "Check them out and see if you're eligible!",
        "",
        "Best regards,",
        "SyrHousing Grant Agent",
        "",
        f"View all grants: {settings.FRONTEND_URL}/programs",
    ])

    subject = f"✨ {len(new_grants)} New Grant(s) Available!"
    body = "\n".join(lines)

    return send_email(user_email, subject, body)


def send_deadline_change_alert(user_email: str, user_name: str, changes: List[Dict]) -> bool:
    """
    Send email alert for grants that had status/deadline changes.
    """
    if not changes:
        return False

    lines = [
        f"Hello {user_name},",
        "",
        f"The following grant program(s) have had recent status changes:",
        "",
    ]

    for item in changes:
        program = item['program']
        status = item['current_status']

        status_icon = "🔴" if status == "closed" else "✅" if status == "open/unknown" else "❓"

        lines.append(f"{status_icon} {program.name}")
        lines.append(f"   Current Status: {status}")

        if program.status_or_deadline:
            lines.append(f"   Deadline Info: {program.status_or_deadline}")
        if program.agency:
            lines.append(f"   Agency: {program.agency}")
        if program.phone:
            lines.append(f"   Phone: {program.phone}")

        lines.append(f"   Check details: {settings.FRONTEND_URL}/programs")
        lines.append("")

    lines.extend([
        "Make sure to verify program availability by calling the agencies directly.",
        "",
        "Best regards,",
        "SyrHousing Grant Agent",
    ])

    subject = f"📢 Grant Status Update: {len(changes)} Change(s) Detected"
    body = "\n".join(lines)

    return send_email(user_email, subject, body)


def run_daily_notifications(db: Session) -> Dict[str, int]:
    """
    Run daily notification check and send alerts to all active users.
    Returns counts of notifications sent.
    """
    # Get data
    closing_soon = get_grants_closing_soon(db, days_threshold=30)
    new_grants = get_new_grants(db, hours_threshold=24)
    deadline_changes = get_recent_deadline_changes(db, hours_threshold=24)

    # Get all users who want notifications (assuming all active users for now)
    users = db.query(User).filter(User.is_active == True).all()

    stats = {
        'closing_soon_sent': 0,
        'new_grants_sent': 0,
        'deadline_changes_sent': 0,
        'total_users': len(users),
        'errors': 0,
    }

    for user in users:
        try:
            # Send closing soon alerts
            if closing_soon:
                if send_closing_soon_alert(user.email, user.full_name, closing_soon):
                    stats['closing_soon_sent'] += 1

            # Send new grants alerts
            if new_grants:
                if send_new_grants_alert(user.email, user.full_name, new_grants):
                    stats['new_grants_sent'] += 1

            # Send deadline change alerts
            if deadline_changes:
                if send_deadline_change_alert(user.email, user.full_name, deadline_changes):
                    stats['deadline_changes_sent'] += 1

        except Exception as e:
            print(f"Error sending notifications to {user.email}: {e}")
            stats['errors'] += 1

    return stats


def send_custom_alert(
    db: Session,
    subject: str,
    message: str,
    user_emails: Optional[List[str]] = None
) -> int:
    """
    Send custom alert to specific users or all users.
    Returns number of emails sent successfully.
    """
    if user_emails:
        users = db.query(User).filter(
            and_(User.email.in_(user_emails), User.is_active == True)
        ).all()
    else:
        users = db.query(User).filter(User.is_active == True).all()

    sent_count = 0

    for user in users:
        try:
            body = f"Hello {user.full_name},\n\n{message}\n\nBest regards,\nSyrHousing Grant Agent"
            if send_email(user.email, subject, body):
                sent_count += 1
        except Exception as e:
            print(f"Error sending custom alert to {user.email}: {e}")

    return sent_count


def send_discovery_notification(db: Session, run: DiscoveryRun) -> int:
    """
    Send email notification to admin users about discovery run results.

    Args:
        db: Database session
        run: Completed DiscoveryRun record

    Returns:
        Number of emails sent successfully
    """
    # Get admin users
    admins = db.query(User).filter(
        and_(User.is_active == True, User.is_admin == True)
    ).all()

    if not admins:
        return 0

    # Get high-confidence grants from this run
    high_confidence_grants = db.query(DiscoveredGrant).filter(
        and_(
            DiscoveredGrant.review_status == "pending",
            DiscoveredGrant.confidence_score >= 0.8,
            DiscoveredGrant.discovered_at >= run.started_at
        )
    ).order_by(DiscoveredGrant.confidence_score.desc()).limit(10).all()

    # Get urgent grants (with deadlines soon)
    urgent_grants = []
    now = datetime.now()

    for grant in high_confidence_grants:
        if grant.status_or_deadline:
            deadline_date = parse_deadline_date(grant.status_or_deadline)
            if deadline_date:
                days_remaining = (deadline_date - now).days
                if 0 <= days_remaining <= 30:
                    urgent_grants.append({
                        'grant': grant,
                        'days_remaining': days_remaining
                    })

    # Build email body
    lines = [
        "Hello Admin,",
        "",
        "🔍 Automated Grant Discovery Completed",
        "",
        "=" * 60,
        "DISCOVERY RUN SUMMARY",
        "=" * 60,
        "",
        f"Run ID: {run.id}",
        f"Status: {run.status.upper()}",
        f"Started: {run.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Completed: {run.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC') if run.completed_at else 'N/A'}",
        "",
        f"✅ Sources Checked: {run.sources_checked}",
        f"🆕 New Grants Discovered: {run.grants_discovered}",
        f"🔄 Duplicates Detected: {run.duplicates_found}",
        f"⚠️ Errors: {run.errors}",
        "",
    ]

    # Add error details if any
    if run.errors > 0:
        lines.extend([
            "=" * 60,
            "⚠️ ERRORS ENCOUNTERED",
            "=" * 60,
            "",
            f"View full error log in discovery run details: {settings.FRONTEND_URL}/admin/discovery/runs/{run.id}",
            "",
        ])

    # Add high-confidence grants section
    if high_confidence_grants:
        lines.extend([
            "=" * 60,
            f"⭐ HIGH-CONFIDENCE GRANTS ({len(high_confidence_grants)} found)",
            "=" * 60,
            "",
            "The following grants have high data quality (>80% confidence) and are ready for review:",
            "",
        ])

        for grant in high_confidence_grants:
            lines.append(f"📋 {grant.name}")
            lines.append(f"   Confidence: {grant.confidence_score:.0%}")
            lines.append(f"   Source: {grant.source_type}")

            if grant.agency:
                lines.append(f"   Agency: {grant.agency}")
            if grant.jurisdiction:
                lines.append(f"   Jurisdiction: {grant.jurisdiction}")
            if grant.max_benefit:
                lines.append(f"   Benefit: {grant.max_benefit}")
            if grant.status_or_deadline:
                lines.append(f"   Deadline: {grant.status_or_deadline}")
            if grant.phone:
                lines.append(f"   Phone: {grant.phone}")
            if grant.email:
                lines.append(f"   Email: {grant.email}")
            if grant.website:
                lines.append(f"   Website: {grant.website}")

            lines.append(f"   Review: {settings.FRONTEND_URL}/admin/discovery/grants/{grant.id}")
            lines.append("")

    # Add urgent deadlines section
    if urgent_grants:
        lines.extend([
            "=" * 60,
            f"🔴 URGENT: GRANTS WITH UPCOMING DEADLINES ({len(urgent_grants)} found)",
            "=" * 60,
            "",
        ])

        for item in urgent_grants:
            grant = item['grant']
            days = item['days_remaining']
            urgency = "🔴 CRITICAL" if days <= 7 else "⚠️ Soon"

            lines.append(f"{urgency} - {grant.name}")
            lines.append(f"   Deadline: {grant.status_or_deadline}")
            lines.append(f"   Days Remaining: {days}")
            lines.append(f"   Review: {settings.FRONTEND_URL}/admin/discovery/grants/{grant.id}")
            lines.append("")

    # Add action items
    lines.extend([
        "=" * 60,
        "📝 ACTION REQUIRED",
        "=" * 60,
        "",
        f"Please review {run.grants_discovered} pending grant(s) in the admin dashboard.",
        "",
        "Actions available:",
        "  • Approve grants to create Program records",
        "  • Reject grants that aren't relevant",
        "  • Mark grants as duplicates of existing programs",
        "",
        f"View all pending grants: {settings.FRONTEND_URL}/admin/discovery/grants?status=pending",
        f"View discovery runs: {settings.FRONTEND_URL}/admin/discovery/runs",
        "",
        "Best regards,",
        "SyrHousing Automated Discovery System",
    ])

    subject = f"🔍 Grant Discovery: {run.grants_discovered} New Grant(s) Found"
    if urgent_grants:
        subject += f" ({len(urgent_grants)} Urgent)"

    body = "\n".join(lines)

    # Send to all admins
    sent_count = 0
    for admin in admins:
        try:
            if send_email(admin.email, subject, body):
                sent_count += 1
        except Exception as e:
            print(f"Error sending discovery notification to {admin.email}: {e}")

    return sent_count
