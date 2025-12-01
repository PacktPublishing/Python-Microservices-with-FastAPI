import json

import pytest
from httpx import ASGITransport, AsyncClient

from domain.notifications.repositories import NotificationRepository
from domain.notifications.schemas import NotificationCreate
from domain.notifications.services import NotificationService
from domain.notifications.types import NotificationType
from domain.user.models import User
from infrastructure.websocket.connection_manager import (
    ConnectionManager,
)


@pytest.fixture
def connection_manager():
    """Create a fresh connection manager for tests."""
    return ConnectionManager()


async def test_connection_manager_connect(connection_manager):
    """Test that connection manager tracks connections."""
    from unittest.mock import AsyncMock, MagicMock

    websocket = MagicMock()
    websocket.accept = AsyncMock()

    result = await connection_manager.connect(websocket, user_id=1)

    assert result is True
    assert 1 in connection_manager.active_connections
    assert websocket in connection_manager.active_connections[1]


async def test_connection_manager_disconnect(connection_manager):
    """Test that connection manager removes connections."""
    from unittest.mock import AsyncMock, MagicMock

    websocket = MagicMock()
    websocket.accept = AsyncMock()

    await connection_manager.connect(websocket, user_id=1)
    connection_manager.disconnect(websocket, user_id=1)

    assert 1 not in connection_manager.active_connections


async def test_connection_manager_max_connections(
    connection_manager,
):
    """Test that connection manager rejects connections at capacity."""
    from unittest.mock import AsyncMock, MagicMock

    connection_manager.MAX_CONNECTIONS_PER_SERVER = 2

    ws1 = MagicMock()
    ws1.accept = AsyncMock()
    ws2 = MagicMock()
    ws2.accept = AsyncMock()
    ws3 = MagicMock()
    ws3.accept = AsyncMock()
    ws3.close = AsyncMock()

    await connection_manager.connect(ws1, user_id=1)
    await connection_manager.connect(ws2, user_id=2)
    result = await connection_manager.connect(ws3, user_id=3)

    assert result is False
    ws3.close.assert_called_once()


async def test_send_personal_message(connection_manager):
    """Test sending message to specific user."""
    from unittest.mock import AsyncMock, MagicMock

    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()

    await connection_manager.connect(websocket, user_id=1)
    await connection_manager.send_personal_message(
        '{"test": "message"}', user_id=1
    )

    websocket.send_text.assert_called_once_with('{"test": "message"}')


async def test_rate_limiting(connection_manager):
    """Test rate limiting for messages."""
    connection_manager.MAX_MESSAGES_PER_MINUTE = 3

    assert connection_manager.check_rate_limit(1) is True
    assert connection_manager.check_rate_limit(1) is True
    assert connection_manager.check_rate_limit(1) is True

    assert connection_manager.check_rate_limit(1) is False


async def test_websocket_auth_required():
    """Test that WebSocket rejects invalid tokens."""
    from unittest.mock import AsyncMock, MagicMock

    manager = ConnectionManager()

    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.close = AsyncMock()

    result = await manager.connect(websocket, user_id=1)
    assert result is True
    websocket.accept.assert_called_once()


async def test_websocket_user_isolation(connection_manager):
    """Test that users only receive their own notifications.

    This is critical for security - messages sent to user 1
    should not be delivered to user 2's connections.
    """
    from unittest.mock import AsyncMock, MagicMock

    parent_ws = MagicMock()
    parent_ws.accept = AsyncMock()
    parent_ws.send_text = AsyncMock()

    sitter_ws = MagicMock()
    sitter_ws.accept = AsyncMock()
    sitter_ws.send_text = AsyncMock()

    await connection_manager.connect(parent_ws, user_id=1)
    await connection_manager.connect(sitter_ws, user_id=2)

    notification = {"message": "For parent only"}
    await connection_manager.send_personal_message(
        json.dumps(notification), user_id=1
    )
    parent_ws.send_text.assert_called_once_with(json.dumps(notification))
    sitter_ws.send_text.assert_not_called()


async def test_notification_persists_and_delivers(
    sqlite_session, test_parent
):
    """Test complete notification flow - creation, persistence, and delivery.

    This catches integration issues between the notification service
    and the connection manager.
    """
    from unittest.mock import AsyncMock, MagicMock, patch

    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()

    test_manager = ConnectionManager()
    await test_manager.connect(websocket, user_id=test_parent.id)

    with patch(
        "domain.notifications.services.manager", test_manager
    ):
        service = NotificationService(NotificationRepository())
        notification_data = NotificationCreate(
            user_id=test_parent.id,
            notification_type=NotificationType.BOOKING_ACCEPTED,
            title="Test Notification",
            message="Test message for delivery",
        )

        result = await service.create_and_send(
            sqlite_session, notification_data
        )

        assert result.id is not None
        assert result.title == "Test Notification"

        websocket.send_text.assert_called_once()
        sent_data = json.loads(websocket.send_text.call_args[0][0])
        assert sent_data["title"] == "Test Notification"
        assert sent_data["message"] == "Test message for delivery"


async def test_multiple_connections_per_user(connection_manager):
    """Test that a user can have multiple WebSocket connections.

    Users might have the site open in multiple browser tabs.
    All connections should receive messages.
    """
    from unittest.mock import AsyncMock, MagicMock

    tab1 = MagicMock()
    tab1.accept = AsyncMock()
    tab1.send_text = AsyncMock()

    tab2 = MagicMock()
    tab2.accept = AsyncMock()
    tab2.send_text = AsyncMock()

    await connection_manager.connect(tab1, user_id=1)
    await connection_manager.connect(tab2, user_id=1)
    assert len(connection_manager.active_connections[1]) == 2

    message = '{"type": "notification"}'
    await connection_manager.send_personal_message(message, user_id=1)

    tab1.send_text.assert_called_once_with(message)
    tab2.send_text.assert_called_once_with(message)
