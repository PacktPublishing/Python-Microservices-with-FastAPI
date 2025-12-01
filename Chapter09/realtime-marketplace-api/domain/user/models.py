from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.models import TimestampMixin
from infrastructure.database.session import Base

from .types import UserRole, UserStatus


class User(Base, TimestampMixin):
    """User model representing marketplace users."""

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    id: Mapped[int] = mapped_column(
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
        init=False,
    )
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole),
        default=UserRole.PARENT,
        nullable=False,
        index=True,
    )
    status: Mapped[UserStatus] = mapped_column(
        SqlEnum(UserStatus),
        default=UserStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        init=False,
    )
