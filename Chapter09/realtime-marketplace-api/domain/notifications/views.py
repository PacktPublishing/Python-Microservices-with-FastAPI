from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from domain.user.dependencies import get_current_user
from domain.user.models import User
from infrastructure.database.session import get_async_session

from .repositories import NotificationRepository
from .schemas import NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notification_repository() -> NotificationRepository:
    """Get notification repository instance."""
    return NotificationRepository()


@router.get("/unread", response_model=list[NotificationRead])
async def get_unread_notifications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    repo: NotificationRepository = Depends(get_notification_repository),
):
    """Get all unread notifications for the current user."""
    notifications = await repo.get_unread_for_user(
        session, current_user.id
    )
    return notifications


@router.get("/", response_model=list[NotificationRead])
async def get_all_notifications(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    repo: NotificationRepository = Depends(get_notification_repository),
):
    """Get all notifications for the current user."""
    notifications = await repo.get_all_for_user(
        session, current_user.id, skip, limit
    )
    return notifications


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    repo: NotificationRepository = Depends(get_notification_repository),
):
    """Mark a notification as read."""
    success = await repo.mark_as_read(
        session, notification_id, current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=404, detail="Notification not found"
        )
    return {"status": "marked as read"}


@router.patch("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    repo: NotificationRepository = Depends(get_notification_repository),
):
    """Mark all notifications as read for the current user."""
    count = await repo.mark_all_as_read(session, current_user.id)
    return {"status": "success", "marked_count": count}
