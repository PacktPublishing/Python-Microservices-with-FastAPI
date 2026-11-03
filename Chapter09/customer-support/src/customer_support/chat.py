from collections.abc import AsyncIterator
from uuid import UUID

from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import UsageLimits

from .config import LLMSettings
from .conversations import (
    ConversationConflict,
    ConversationNotFound,
    ConversationRepository,
)
from .knowledge import KnowledgeBase


class Answer(BaseModel):
    """Final text and new messages, including retrieval evidence."""

    text: str
    messages: list[ModelMessage]


class SupportChat:
    """Load owned history, run the agent and save only new messages."""

    def __init__(
        self,
        agent: Agent[KnowledgeBase, str],
        knowledge: KnowledgeBase,
        repository: ConversationRepository,
        settings: LLMSettings,
    ) -> None:
        """Receive dependencies without coupling orchestration to HTTP."""
        self.agent = agent
        self.knowledge = knowledge
        self.repository = repository
        self.settings = settings

    async def _history(
        self, user_id: str, conversation_id: UUID, position: int
    ) -> list[ModelMessage]:
        """Load owned history and check it has `position` messages."""
        history = await self.repository.load(
            user_id, conversation_id
        )
        if history is None:
            raise ConversationNotFound("Conversation not found")
        if len(history.messages) != position:
            raise ConversationConflict(
                "Conversation changed; reload before retrying"
            )
        return history.messages

    async def stream(
        self,
        user_id: str,
        conversation_id: UUID,
        question: str,
        *,
        expected_position: int,
    ) -> AsyncIterator[str]:
        """Check access now, then return a stream of text deltas.

        The new messages are saved once the stream is exhausted.

        Raises:
            ConversationNotFound: The caller cannot access this conversation.
            ConversationConflict: History changed since `expected_position`.
        """
        history = await self._history(
            user_id, conversation_id, expected_position
        )

        async def deltas() -> AsyncIterator[str]:
            async with self.agent.run_stream(
                question,
                deps=self.knowledge,
                message_history=history,
                usage_limits=UsageLimits(
                    request_limit=self.settings.request_limit
                ),
            ) as result:
                text = result.stream_text(delta=True)
                async for delta in text:
                    yield delta
            await self.repository.append(
                user_id,
                conversation_id,
                result.new_messages(),
                expected_position=expected_position,
            )

        return deltas()

    async def answer(
        self,
        user_id: str,
        conversation_id: UUID,
        question: str,
        *,
        expected_position: int,
    ) -> Answer:
        """Continue an owned conversation and persist the completed turn.

        Raises:
            ConversationNotFound: The caller cannot access this conversation.
            ConversationConflict: History changed while the agent was running.
            UsageLimitExceeded: The run exceeded the configured request limit.
        """
        history = await self._history(
            user_id, conversation_id, expected_position
        )
        result = await self.agent.run(
            question,
            deps=self.knowledge,
            message_history=history,
            usage_limits=UsageLimits(
                request_limit=self.settings.request_limit
            ),
        )
        messages = result.new_messages()
        await self.repository.append(
            user_id,
            conversation_id,
            messages,
            expected_position=expected_position,
        )
        logger.debug(
            "Completed support run in {} requests",
            result.usage.requests,
        )
        return Answer(text=result.output, messages=messages)
