from datetime import datetime

from pydantic import BaseModel

from .types import NotificationType


class NotificationBase(BaseModel):
    """Base schema for notifications."""

    user_id: int
    notification_type: NotificationType
    title: str
    message: str
    related_booking_id: int | None = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""

    pass


class NotificationRead(NotificationBase):
    """Schema for reading a notification."""

    id: int
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""

    is_read: bool | None = None
