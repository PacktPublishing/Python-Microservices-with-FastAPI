from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.models import TimestampMixin
from infrastructure.database.session import Base

from .types import UserRole, UserStatus

if TYPE_CHECKING:
    from domain.user.models import ParentProfile, SitterProfile


class User(Base, TimestampMixin):
    """User model representing marketplace users."""

    __tablename__ = "users"

    # Required fields (no defaults) come first
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

    # Fields with defaults
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
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )
    profile_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
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

    parent_profile: Mapped["ParentProfile | None"] = relationship(
        "ParentProfile",
        back_populates="user",
        uselist=False,
        default=None,
        init=False,
    )
    sitter_profile: Mapped["SitterProfile | None"] = relationship(
        "SitterProfile",
        back_populates="user",
        uselist=False,
        default=None,
        init=False,
    )


class ParentProfile(Base, TimestampMixin):
    """Profile for parent users."""

    __tablename__ = "parent_profiles"

    # Required field first
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Fields with defaults
    id: Mapped[int] = mapped_column(
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
        init=False,
    )
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    number_of_children: Mapped[int | None] = mapped_column(
        nullable=True,
        default=None,
    )
    children_age_range: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )
    max_hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        default=None,
    )
    address_street: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    address_city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )
    address_state: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )
    address_zip: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )
    special_requirements: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    has_pets: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    pets_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="parent_profile",
        default=None,
        init=False,
    )


class SitterProfile(Base, TimestampMixin):
    """Profile for sitter users."""

    __tablename__ = "sitter_profiles"

    # Required field first
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Fields with defaults
    id: Mapped[int] = mapped_column(
        autoincrement=True,
        nullable=False,
        unique=True,
        primary_key=True,
        init=False,
    )
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    birth_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )
    hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        default=None,
    )
    years_of_experience: Mapped[int | None] = mapped_column(
        nullable=True,
        default=None,
    )
    has_transportation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    max_travel_distance: Mapped[int | None] = mapped_column(
        nullable=True,
        default=None,
    )
    address_city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )
    address_state: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )
    background_check_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    background_check_date: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True),
            nullable=True,
            default=None,
        )
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="sitter_profile",
        default=None,
        init=False,
    )
