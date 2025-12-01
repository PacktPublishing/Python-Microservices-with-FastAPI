from enum import Enum


class BookingStatus(str, Enum):
    """Status of a booking."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
