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
        history = await self.repository.load(
            user_id, conversation_id
        )
        if history is None:
            raise ConversationNotFound("Conversation not found")
        if len(history.messages) != expected_position:
            raise ConversationConflict(
                "Conversation changed; reload before retrying"
            )
        result = await self.agent.run(
            question,
            deps=self.knowledge,
            message_history=history.messages,
            usage_limits=UsageLimits(
                request_limit=self.settings.request_limit
            ),
        )
        messages = result.new_messages()
        await self.repository.append(
            user_id,
            conversation_id,
            messages,
            expected_position=len(history.messages),
        )
        logger.debug(
            "Completed support run in {} requests",
            result.usage.requests,
        )
        return Answer(text=result.output, messages=messages)
