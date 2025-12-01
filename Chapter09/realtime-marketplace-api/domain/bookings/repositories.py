from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Booking
from .schemas import BookingCreate
from .types import BookingStatus


class BookingRepository:
    """Repository for booking database operations."""

    async def create(
        self,
        session: AsyncSession,
        booking_data: BookingCreate,
        parent_id: int,
    ) -> Booking:
        """Create a new booking."""
        booking = Booking(
            parent_id=parent_id,
            sitter_id=booking_data.sitter_id,
            start_time=booking_data.start_time,
            end_time=booking_data.end_time,
            hourly_rate=booking_data.hourly_rate,
            notes=booking_data.notes,
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        return booking

    async def get(
        self,
        session: AsyncSession,
        booking_id: int,
    ) -> Booking | None:
        """Get a booking by ID."""
        stmt = select(Booking).where(Booking.id == booking_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        session: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Booking]:
        """Get all bookings for a user (as parent or sitter)."""
        stmt = (
            select(Booking)
            .where(
                (Booking.parent_id == user_id)
                | (Booking.sitter_id == user_id)
            )
            .order_by(Booking.start_time.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        session: AsyncSession,
        booking: Booking,
        status: BookingStatus,
    ) -> Booking:
        """Update a booking's status."""
        booking.status = status
        await session.commit()
        await session.refresh(booking)
        return booking
