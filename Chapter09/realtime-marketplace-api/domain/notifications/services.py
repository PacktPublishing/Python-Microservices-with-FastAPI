import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.websocket.connection_manager import manager

from .models import Notification
from .repositories import NotificationRepository
from .schemas import NotificationCreate, NotificationRead

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    def _notification_to_dict(self, notification: Notification) -> dict:
        """Convert a notification to a dictionary."""
        return {
            "id": notification.id,
            "type": notification.notification_type.value,
            "title": notification.title,
            "message": notification.message,
            "created_at": notification.created_at.isoformat(),
        }

    async def _try_local_delivery(
        self,
        notification_dict: dict,
        user_id: int,
    ) -> bool:
        """Try to deliver notification to locally connected user."""
        try:
            await manager.send_personal_message(
                json.dumps(notification_dict),
                user_id,
            )
            logger.info(
                f"Delivered notification {notification_dict['id']} "
                f"locally to user {user_id}"
            )
            return True
        except Exception as e:
            logger.debug(
                f"User {user_id} not connected to this server: {e}"
            )
            return False

    async def create_and_send(
        self,
        session: AsyncSession,
        notification_data: NotificationCreate,
    ) -> NotificationRead:
        """Create a notification and try to deliver it."""
        notification = await self.repository.create(
            session, notification_data
        )

        notification_dict = self._notification_to_dict(notification)

        await self._try_local_delivery(
            notification_dict,
            notification_data.user_id,
        )

        await manager.publish_notification(
            notification_dict,
            notification_data.user_id,
        )

        return NotificationRead.model_validate(notification)
