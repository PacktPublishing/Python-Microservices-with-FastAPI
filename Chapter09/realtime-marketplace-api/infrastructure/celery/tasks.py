import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from celery import Task

from infrastructure.config.settings import settings

from .celery_app import celery_app


class EmailTask(Task):
    """Base task class for email operations."""

    pass


def _create_parent_booking_message(
    parent_name: str,
    sitter_name: str,
    booking_time: str,
    booking_id: int,
) -> str:
    """Create email body for parent booking confirmation."""
    return f"""
Hi {parent_name},

Your booking with {sitter_name} is confirmed!
Date and time: {booking_time}
Booking ID: {booking_id}

Thank you for using our marketplace!
"""


def _create_sitter_booking_message(
    sitter_name: str,
    parent_name: str,
    booking_time: str,
    booking_id: int,
) -> str:
    """Create email body for sitter booking notification."""
    return f"""
Hi {sitter_name},

You have a new booking request from {parent_name}!
Date and time: {booking_time}
Booking ID: {booking_id}

Please log in to accept or decline this booking.
"""


def _send_email(subject: str, recipient: str, body: str) -> None:
    """Send an email using SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = recipient
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


@celery_app.task(
    bind=True,
    base=EmailTask,
    autoretry_for=(smtplib.SMTPException,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
)
def send_booking_confirmation_to_parent(
    self,
    booking_id: int,
    parent_email: str,
    parent_name: str,
    sitter_name: str,
    booking_time: str,
):
    """Send booking confirmation email to parent."""
    body = _create_parent_booking_message(
        parent_name, sitter_name, booking_time, booking_id
    )
    _send_email(
        subject="Booking Confirmed!",
        recipient=parent_email,
        body=body,
    )
    return {"status": "sent", "booking_id": booking_id}


@celery_app.task(
    bind=True,
    base=EmailTask,
    autoretry_for=(smtplib.SMTPException,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
)
def send_booking_notification_to_sitter(
    self,
    booking_id: int,
    sitter_email: str,
    sitter_name: str,
    parent_name: str,
    booking_time: str,
):
    """Send booking notification email to sitter."""
    body = _create_sitter_booking_message(
        sitter_name, parent_name, booking_time, booking_id
    )
    _send_email(
        subject="New Booking Request",
        recipient=sitter_email,
        body=body,
    )
    return {"status": "sent", "booking_id": booking_id}


@celery_app.task
def send_booking_reminders():
    """Send reminders for bookings happening in 24 hours."""
    # This would query the database for upcoming bookings
    # and send reminder emails to both parents and sitters
    return {"status": "completed", "reminders_sent": 0}
