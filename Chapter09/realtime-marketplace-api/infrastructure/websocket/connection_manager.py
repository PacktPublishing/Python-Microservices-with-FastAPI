import asyncio
import json
import logging
import time

import redis.asyncio as redis
from fastapi import WebSocket

from infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""

    MAX_CONNECTIONS_PER_SERVER = 5000
    MAX_MESSAGES_PER_MINUTE = 60

    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}
        self._total_connections = 0
        self.message_counts: dict[int, list[float]] = {}
        self.redis_client: redis.Redis | None = None
        self.pubsub: redis.client.PubSub | None = None

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
    ) -> bool:
        """Accept a WebSocket connection for a user."""
        if self._total_connections >= self.MAX_CONNECTIONS_PER_SERVER:
            await websocket.close(
                code=1008,
                reason="Server at capacity",
            )
            return False

        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        self._total_connections += 1

        logger.info(
            f"User {user_id} connected. "
            f"Total connections: {self._total_connections}"
        )
        return True

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection for a user."""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                self._total_connections -= 1
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info(
            f"User {user_id} disconnected. "
            f"Total connections: {self._total_connections}"
        )

    async def send_personal_message(
        self,
        message: str,
        user_id: int,
    ):
        """Send a message to all connections for a specific user."""
        if user_id not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(
                    f"Failed to send message to user {user_id}: {e}"
                )
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn, user_id)

    def check_rate_limit(self, user_id: int) -> bool:
        """Check if a user has exceeded the rate limit."""
        now = time.time()
        if user_id not in self.message_counts:
            self.message_counts[user_id] = []

        self.message_counts[user_id] = [
            ts
            for ts in self.message_counts[user_id]
            if now - ts < 60
        ]

        if (
            len(self.message_counts[user_id])
            >= self.MAX_MESSAGES_PER_MINUTE
        ):
            return False

        self.message_counts[user_id].append(now)
        return True

    async def publish_notification(
        self,
        notification_dict: dict,
        user_id: int,
    ):
        """Publish a notification to Redis for multi-server support."""
        if self.redis_client is None:
            return

        message = {
            "user_id": user_id,
            "notification": notification_dict,
        }
        await self.redis_client.publish(
            "notifications",
            json.dumps(message),
        )

    async def _listen_for_messages(self):
        """Listen for messages from Redis pub/sub."""
        if self.pubsub is None:
            return

        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    user_id = data["user_id"]
                    notification = data["notification"]

                    await self.send_personal_message(
                        json.dumps(notification),
                        user_id,
                    )
                except Exception as e:
                    logger.error(f"Error processing pub/sub message: {e}")

    async def start_listening(self):
        """Start listening for Redis pub/sub notifications."""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
            )
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe("notifications")
            asyncio.create_task(self._listen_for_messages())
            logger.info("Started Redis pub/sub listener")
        except Exception as e:
            logger.warning(
                f"Could not connect to Redis for pub/sub: {e}. "
                "Multi-server notifications will not work."
            )

    async def shutdown(self):
        """Clean up connections on shutdown."""
        if self.pubsub:
            await self.pubsub.unsubscribe("notifications")
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()

        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.close()
                except Exception:
                    pass

        self.active_connections.clear()
        self._total_connections = 0
        logger.info("Connection manager shut down")


manager = ConnectionManager()
