from enum import Enum


class NotificationType(str, Enum):
    """Types of notifications in the marketplace."""

    BOOKING_CREATED = "booking_created"
    BOOKING_ACCEPTED = "booking_accepted"
    BOOKING_DECLINED = "booking_declined"
    BOOKING_CANCELLED = "booking_cancelled"
    EMAIL_SENT = "email_sent"
