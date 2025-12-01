from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Notification
from .schemas import NotificationCreate


class NotificationRepository:
    """Repository for notification database operations."""

    async def create(
        self,
        session: AsyncSession,
        notification_data: NotificationCreate,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=notification_data.user_id,
            notification_type=notification_data.notification_type,
            title=notification_data.title,
            message=notification_data.message,
            related_booking_id=notification_data.related_booking_id,
        )
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        return notification

    async def get(
        self,
        session: AsyncSession,
        notification_id: int,
    ) -> Notification | None:
        """Get a notification by ID."""
        stmt = select(Notification).where(
            Notification.id == notification_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_unread_for_user(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 50,
    ) -> list[Notification]:
        """Get unread notifications for a user."""
        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_for_user(
        self,
        session: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Notification]:
        """Get all notifications for a user with pagination."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_read(
        self,
        session: AsyncSession,
        notification_id: int,
        user_id: int,
    ) -> bool:
        """Mark a notification as read."""
        stmt = (
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .values(is_read=True)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0

    async def mark_all_as_read(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> int:
        """Mark all notifications as read for a user."""
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount
