"""
Email notification service using SendGrid.
Falls back silently when SendGrid is not configured (SENDGRID_API_KEY empty).
"""

import logging
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from sendgrid import SendGridAPIClient
        _client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    return _client


def is_email_available() -> bool:
    return bool(settings.SENDGRID_API_KEY)


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an email via SendGrid. Returns True on success, False on failure."""
    if not is_email_available():
        logger.info("SendGrid not configured, skipping email to %s: %s", to_email, subject)
        return False

    try:
        from sendgrid.helpers.mail import Mail
        message = Mail(
            from_email=(settings.SENDER_EMAIL, settings.SENDER_NAME),
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
        response = _get_client().send(message)
        logger.info("Email sent to %s (status %s): %s", to_email, response.status_code, subject)
        return 200 <= response.status_code < 300
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, str(e))
        return False


# --- Email Templates ---

def _base_template(content: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #1e3a5f; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">SyrHousing</h1>
            <p style="color: #a0c4e8; margin: 4px 0 0 0; font-size: 13px;">DJ AI Business Consultant</p>
        </div>
        <div style="background: #ffffff; border: 1px solid #e5e7eb; border-top: none; padding: 24px; border-radius: 0 0 8px 8px;">
            {content}
        </div>
        <div style="text-align: center; padding: 16px; color: #9ca3af; font-size: 12px;">
            <p>DJ AI Business Consultant &middot; Syracuse, NY</p>
            <p>Transforming Business. Rising Above the Challenges.</p>
        </div>
    </div>
    """


def send_welcome_email(email: str, full_name: str, verification_token: str) -> bool:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    content = f"""
        <h2 style="color: #1e3a5f; margin-top: 0;">Welcome, {full_name}!</h2>
        <p>Thank you for joining SyrHousing. We help Syracuse-area homeowners and seniors
        find home repair grants and assistance programs.</p>
        <p>Please verify your email address to get the most out of your account:</p>
        <div style="text-align: center; margin: 24px 0;">
            <a href="{verify_url}"
               style="background-color: #1e3a5f; color: white; padding: 12px 32px;
                      text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                Verify Email
            </a>
        </div>
        <p style="color: #6b7280; font-size: 13px;">
            Or copy this link: <a href="{verify_url}" style="color: #2d6a9f;">{verify_url}</a>
        </p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
        <p style="color: #6b7280; font-size: 13px;">
            <strong>Get started:</strong> Browse available programs, chat with our AI assistant,
            and track your grant applications all in one place.
        </p>
    """
    return send_email(email, "Welcome to SyrHousing - Verify Your Email", _base_template(content))


def send_verification_email(email: str, full_name: str, verification_token: str) -> bool:
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    content = f"""
        <h2 style="color: #1e3a5f; margin-top: 0;">Verify Your Email</h2>
        <p>Hi {full_name}, please click below to verify your email address:</p>
        <div style="text-align: center; margin: 24px 0;">
            <a href="{verify_url}"
               style="background-color: #1e3a5f; color: white; padding: 12px 32px;
                      text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                Verify Email
            </a>
        </div>
        <p style="color: #6b7280; font-size: 13px;">This link expires in 24 hours.</p>
    """
    return send_email(email, "SyrHousing - Verify Your Email", _base_template(content))


def send_application_submitted(email: str, full_name: str, program_name: str) -> bool:
    content = f"""
        <h2 style="color: #1e3a5f; margin-top: 0;">Application Submitted</h2>
        <p>Hi {full_name},</p>
        <p>Your application for <strong>{program_name}</strong> has been submitted successfully.</p>
        <div style="background: #f0f9ff; border-left: 4px solid #4a9eda; padding: 12px 16px; margin: 16px 0; border-radius: 0 4px 4px 0;">
            <p style="margin: 0; color: #1e3a5f;"><strong>Next steps:</strong></p>
            <ul style="margin: 8px 0; padding-left: 20px; color: #374151;">
                <li>Your application will be reviewed</li>
                <li>You'll be notified of any status changes</li>
                <li>Check your dashboard for updates</li>
            </ul>
        </div>
        <div style="text-align: center; margin: 24px 0;">
            <a href="{settings.FRONTEND_URL}/applications"
               style="background-color: #1e3a5f; color: white; padding: 12px 32px;
                      text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                View My Applications
            </a>
        </div>
    """
    return send_email(email, f"Application Submitted - {program_name}", _base_template(content))


def send_application_status_update(
    email: str, full_name: str, program_name: str, new_status: str, notes: Optional[str] = None
) -> bool:
    status_messages = {
        "under_review": ("Under Review", "#d97706", "Your application is now being reviewed."),
        "approved": ("Approved!", "#059669", "Congratulations! Your application has been approved."),
        "denied": ("Not Approved", "#dc2626", "Unfortunately, your application was not approved at this time."),
        "withdrawn": ("Withdrawn", "#6b7280", "Your application has been withdrawn."),
    }

    label, color, message = status_messages.get(
        new_status, (new_status.replace("_", " ").title(), "#6b7280", f"Your application status has changed to {new_status}.")
    )

    notes_html = ""
    if notes:
        notes_html = f"""
        <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 12px 16px; margin: 16px 0; border-radius: 4px;">
            <p style="margin: 0; color: #6b7280; font-size: 13px;"><strong>Notes:</strong> {notes}</p>
        </div>
        """

    content = f"""
        <h2 style="color: #1e3a5f; margin-top: 0;">Application Update</h2>
        <p>Hi {full_name},</p>
        <p>{message}</p>
        <div style="text-align: center; margin: 20px 0;">
            <div style="display: inline-block; background: {color}20; border: 2px solid {color};
                        padding: 8px 24px; border-radius: 24px;">
                <span style="color: {color}; font-weight: bold; font-size: 16px;">{label}</span>
            </div>
        </div>
        <p><strong>Program:</strong> {program_name}</p>
        {notes_html}
        <div style="text-align: center; margin: 24px 0;">
            <a href="{settings.FRONTEND_URL}/applications"
               style="background-color: #1e3a5f; color: white; padding: 12px 32px;
                      text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                View Details
            </a>
        </div>
    """
    return send_email(email, f"Application {label} - {program_name}", _base_template(content))


def send_password_reset(email: str, full_name: str, reset_token: str) -> bool:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    content = f"""
        <h2 style="color: #1e3a5f; margin-top: 0;">Reset Your Password</h2>
        <p>Hi {full_name},</p>
        <p>We received a request to reset your password. Click below to set a new password:</p>
        <div style="text-align: center; margin: 24px 0;">
            <a href="{reset_url}"
               style="background-color: #1e3a5f; color: white; padding: 12px 32px;
                      text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                Reset Password
            </a>
        </div>
        <p style="color: #6b7280; font-size: 13px;">This link expires in 1 hour.
        If you didn't request this, you can safely ignore this email.</p>
    """
    return send_email(email, "SyrHousing - Reset Your Password", _base_template(content))
