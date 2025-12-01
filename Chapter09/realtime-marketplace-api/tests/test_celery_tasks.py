from unittest.mock import MagicMock, patch

import pytest

from infrastructure.celery.tasks import (
    send_booking_confirmation_to_parent,
    send_booking_notification_to_sitter,
)


@pytest.fixture
def mock_smtp():
    """Mock SMTP for testing email tasks."""
    with patch("smtplib.SMTP") as mock:
        mock_server = MagicMock()
        mock.return_value.__enter__.return_value = mock_server
        yield mock_server


def test_send_booking_confirmation_to_parent(
    celery_config, mock_smtp
):
    """Test that booking confirmation email is sent to parent."""
    result = send_booking_confirmation_to_parent(
        booking_id=123,
        parent_email="sarah@example.com",
        parent_name="Sarah",
        sitter_name="Jessica",
        booking_time="December 20, 2024 at 07:00 PM",
    )

    assert mock_smtp.send_message.called
    assert result["status"] == "sent"
    assert result["booking_id"] == 123


def test_send_booking_notification_to_sitter(
    celery_config, mock_smtp
):
    """Test that booking notification email is sent to sitter."""
    result = send_booking_notification_to_sitter(
        booking_id=456,
        sitter_email="jessica@example.com",
        sitter_name="Jessica",
        parent_name="Sarah",
        booking_time="December 20, 2024 at 07:00 PM",
    )

    assert mock_smtp.send_message.called
    assert result["status"] == "sent"
    assert result["booking_id"] == 456


def test_email_contains_correct_content(celery_config, mock_smtp):
    """Test that email contains booking details."""
    send_booking_confirmation_to_parent(
        booking_id=789,
        parent_email="sarah@example.com",
        parent_name="Sarah",
        sitter_name="Jessica",
        booking_time="December 25, 2024 at 06:00 PM",
    )

    call_args = mock_smtp.send_message.call_args
    sent_message = call_args[0][0]

    assert sent_message["Subject"] == "Booking Confirmed!"
    assert sent_message["To"] == "sarah@example.com"
