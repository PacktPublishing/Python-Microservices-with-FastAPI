from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.models import TimestampMixin
from infrastructure.database.session import Base

from .types import NotificationType


class Notification(Base, TimestampMixin):
    """Notification model for persistent notifications."""

    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        SqlEnum(NotificationType),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        init=False,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )
    related_booking_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
