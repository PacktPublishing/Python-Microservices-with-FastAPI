from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.models import TimestampMixin
from infrastructure.database.session import Base

from .types import BookingStatus


class Booking(Base, TimestampMixin):
    """Booking model for babysitter appointments."""

    __tablename__ = "bookings"

    parent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sitter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        init=False,
    )
    status: Mapped[BookingStatus] = mapped_column(
        SqlEnum(BookingStatus),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True,
    )
    hourly_rate: Mapped[float | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        default=None,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
