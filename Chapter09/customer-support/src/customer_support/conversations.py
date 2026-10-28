from datetime import UTC, datetime
from uuid import UUID, uuid4

from loguru import logger
from pydantic import BaseModel, Field, field_validator
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
)
from sqlalchemy import ForeignKey, Text, select, update
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import DatabaseSettings


class Base(DeclarativeBase):
    """Metadata shared by the conversation tables."""


class ConversationRow(Base):
    """Conversation identity, owner and optimistic message position."""

    __tablename__ = "conversations"
    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4
    )
    user_id: Mapped[str] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC)
    )
    message_count: Mapped[int] = mapped_column(default=0)


class MessageRow(Base):
    """One serialized PydanticAI message in conversation order."""

    __tablename__ = "messages"
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id"), primary_key=True
    )
    position: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)


class Conversation(BaseModel):
    """Owner-scoped identity returned without loading the history."""

    id: UUID
    user_id: str
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        """Restore UTC lost by SQLite's timezone-naive datetime storage."""
        return (
            value.replace(tzinfo=UTC)
            if value.tzinfo is None
            else value.astimezone(UTC)
        )


class ConversationHistory(Conversation):
    """A snapshot whose length is used to detect conflicting writes."""

    messages: list[ModelMessage] = Field(default_factory=list)


class ConversationNotFound(LookupError):
    """The conversation does not exist or does not belong to the user."""


class ConversationConflict(RuntimeError):
    """The stored history changed while an answer was being generated."""


class Database:
    """Own the engine and session factory outside the HTTP layer."""

    def __init__(self, settings: DatabaseSettings) -> None:
        """Configure connections without creating tables yet."""
        self.engine = create_async_engine(settings.url)
        self.sessions = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    async def initialize(self) -> None:
        """Create missing tables; safe to call again after a restart."""
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.debug("Conversation database initialized")

    async def close(self) -> None:
        """Release pooled connections when the application stops."""
        await self.engine.dispose()


class ConversationRepository:
    """Persist messages with ownership checks at the storage boundary."""

    def __init__(
        self, sessions: async_sessionmaker[AsyncSession]
    ) -> None:
        """Receive a session factory rather than a shared session."""
        self.sessions = sessions

    async def create(self, user_id: str) -> Conversation:
        """Create a fresh conversation belonging to the given user."""
        async with self.sessions.begin() as session:
            row = ConversationRow(user_id=user_id)
            session.add(row)
            await session.flush()
            return Conversation.model_validate(
                row, from_attributes=True
            )

    async def list_conversations(
        self, user_id: str
    ) -> list[Conversation]:
        """List only the caller's conversations in stable creation order."""
        query = (
            select(ConversationRow)
            .where(ConversationRow.user_id == user_id)
            .order_by(
                ConversationRow.created_at, ConversationRow.id
            )
        )
        async with self.sessions() as session:
            rows = await session.scalars(query)
            return [
                Conversation.model_validate(
                    row, from_attributes=True
                )
                for row in rows
            ]

    async def load(
        self, user_id: str, conversation_id: UUID
    ) -> ConversationHistory | None:
        """Load a consistent history prefix, hiding other users' IDs."""
        query = select(ConversationRow).where(
            ConversationRow.id == conversation_id,
            ConversationRow.user_id == user_id,
        )
        async with self.sessions() as session:
            row = await session.scalar(query)
            if row is None:
                return None
            contents = await session.scalars(
                select(MessageRow.content)
                .where(
                    MessageRow.conversation_id == row.id,
                    MessageRow.position < row.message_count,
                )
                .order_by(MessageRow.position)
            )
            messages = [
                message
                for content in contents
                for message in ModelMessagesTypeAdapter.validate_json(
                    content
                )
            ]
            return ConversationHistory(
                id=row.id,
                user_id=row.user_id,
                created_at=row.created_at,
                messages=messages,
            )

    async def append(
        self,
        user_id: str,
        conversation_id: UUID,
        messages: list[ModelMessage],
        *,
        expected_position: int,
    ) -> None:
        """Atomically append a completed run, rejecting stale histories.

        Args:
            user_id (str): Owner requesting the append.
            conversation_id (UUID): Conversation being continued.
            messages (list[ModelMessage]): Only the new run's messages.
            expected_position (int): Length of the history used by the model.

        Raises:
            ConversationNotFound: Conversation missing or owned by another user.
            ConversationConflict: Another run already changed the history.
        """
        encoded = [
            ModelMessagesTypeAdapter.dump_json([message]).decode()
            for message in messages
        ]
        statement = (
            update(ConversationRow)
            .where(
                ConversationRow.id == conversation_id,
                ConversationRow.user_id == user_id,
                ConversationRow.message_count
                == expected_position,
            )
            .values(
                message_count=expected_position + len(encoded)
            )
            .returning(ConversationRow.id)
        )
        async with self.sessions.begin() as session:
            updated = await session.scalar(statement)
            if updated is None:
                owned = await session.scalar(
                    select(ConversationRow.id).where(
                        ConversationRow.id == conversation_id,
                        ConversationRow.user_id == user_id,
                    )
                )
                if owned is None:
                    raise ConversationNotFound(
                        "Conversation not found"
                    )
                raise ConversationConflict(
                    "Conversation changed; reload before retrying"
                )
            session.add_all(
                [
                    MessageRow(
                        conversation_id=conversation_id,
                        position=expected_position + offset,
                        content=content,
                    )
                    for offset, content in enumerate(encoded)
                ]
            )
        logger.debug(
            "Persisted {} new conversation messages", len(encoded)
        )
