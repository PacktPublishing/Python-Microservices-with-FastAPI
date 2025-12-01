import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from domain.notifications.models import Notification
from domain.notifications.repositories import NotificationRepository
from domain.notifications.schemas import NotificationCreate
from domain.notifications.services import NotificationService
from domain.notifications.types import NotificationType
from domain.user.models import User


async def test_create_notification(
    sqlite_session: AsyncSession, test_parent: User
):
    """Test creating a notification."""
    repo = NotificationRepository()
    notification_data = NotificationCreate(
        user_id=test_parent.id,
        notification_type=NotificationType.BOOKING_CREATED,
        title="Test Notification",
        message="This is a test notification",
    )

    notification = await repo.create(sqlite_session, notification_data)

    assert notification.id is not None
    assert notification.user_id == test_parent.id
    assert notification.title == "Test Notification"
    assert notification.is_read is False


async def test_get_unread_notifications(
    sqlite_session: AsyncSession, test_parent: User
):
    """Test getting unread notifications."""
    repo = NotificationRepository()

    for i in range(3):
        await repo.create(
            sqlite_session,
            NotificationCreate(
                user_id=test_parent.id,
                notification_type=NotificationType.BOOKING_CREATED,
                title=f"Notification {i}",
                message=f"Message {i}",
            ),
        )

    unread = await repo.get_unread_for_user(
        sqlite_session, test_parent.id
    )

    assert len(unread) == 3


async def test_mark_notification_as_read(
    sqlite_session: AsyncSession, test_parent: User
):
    """Test marking a notification as read."""
    repo = NotificationRepository()

    notification = await repo.create(
        sqlite_session,
        NotificationCreate(
            user_id=test_parent.id,
            notification_type=NotificationType.BOOKING_ACCEPTED,
            title="Test",
            message="Test message",
        ),
    )

    success = await repo.mark_as_read(
        sqlite_session, notification.id, test_parent.id
    )

    assert success is True

    unread = await repo.get_unread_for_user(
        sqlite_session, test_parent.id
    )
    assert len(unread) == 0


async def test_mark_all_as_read(
    sqlite_session: AsyncSession, test_parent: User
):
    """Test marking all notifications as read."""
    repo = NotificationRepository()

    for i in range(5):
        await repo.create(
            sqlite_session,
            NotificationCreate(
                user_id=test_parent.id,
                notification_type=NotificationType.BOOKING_CREATED,
                title=f"Notification {i}",
                message=f"Message {i}",
            ),
        )

    count = await repo.mark_all_as_read(
        sqlite_session, test_parent.id
    )

    assert count == 5

    unread = await repo.get_unread_for_user(
        sqlite_session, test_parent.id
    )
    assert len(unread) == 0


async def test_notification_service_create_and_send(
    sqlite_session: AsyncSession, test_parent: User
):
    """Test notification service creates and attempts delivery."""
    repo = NotificationRepository()
    service = NotificationService(repo)

    notification_data = NotificationCreate(
        user_id=test_parent.id,
        notification_type=NotificationType.BOOKING_ACCEPTED,
        title="Booking Accepted",
        message="Your booking was accepted",
        related_booking_id=123,
    )

    result = await service.create_and_send(
        sqlite_session, notification_data
    )

    assert result.id is not None
    assert result.title == "Booking Accepted"
    assert result.related_booking_id == 123


async def test_notification_isolation(
    sqlite_session: AsyncSession,
    test_parent: User,
    test_sitter: User,
):
    """Test that users only see their own notifications."""
    repo = NotificationRepository()

    await repo.create(
        sqlite_session,
        NotificationCreate(
            user_id=test_parent.id,
            notification_type=NotificationType.BOOKING_ACCEPTED,
            title="Parent Notification",
            message="For parent only",
        ),
    )

    await repo.create(
        sqlite_session,
        NotificationCreate(
            user_id=test_sitter.id,
            notification_type=NotificationType.BOOKING_CREATED,
            title="Sitter Notification",
            message="For sitter only",
        ),
    )

    parent_notifications = await repo.get_unread_for_user(
        sqlite_session, test_parent.id
    )
    sitter_notifications = await repo.get_unread_for_user(
        sqlite_session, test_sitter.id
    )

    assert len(parent_notifications) == 1
    assert parent_notifications[0].title == "Parent Notification"

    assert len(sitter_notifications) == 1
    assert sitter_notifications[0].title == "Sitter Notification"
