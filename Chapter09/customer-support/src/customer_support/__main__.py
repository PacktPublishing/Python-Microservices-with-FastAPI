from typing import Self
from uuid import UUID

from pydantic import Field, model_validator
from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliSubCommand,
    SettingsConfigDict,
)

from .agent import build_agent
from .chat import Answer, SupportChat
from .config import KnowledgeSettings, Settings
from .conversations import ConversationRepository, Database
from .knowledge import KnowledgeBase


class Ingest(KnowledgeSettings):
    """Sync the source folder into the knowledge base."""

    def cli_cmd(self) -> None:
        """Open the knowledge base and sync the folder."""
        KnowledgeBase(self).sync()


class ChatResult(Answer):
    """A completed CLI turn with the values needed to resume it."""

    conversation_id: UUID
    next_position: int


class Chat(Settings):
    """Ask a question in a new or existing owned conversation."""

    user_id: str = Field(
        min_length=1,
        description="Local user identity; not authentication.",
    )
    question: str = Field(
        min_length=1, description="Support question to answer."
    )
    conversation_id: UUID | None = Field(
        None, description="Existing conversation to continue."
    )
    expected_position: int | None = Field(
        None,
        ge=0,
        description="Required stored message count when resuming.",
    )

    @model_validator(mode="after")
    def check_resume(self) -> Self:
        """Require a history position exactly when resuming a conversation."""
        if (self.conversation_id is None) != (
            self.expected_position is None
        ):
            raise ValueError(
                "conversation-id and expected-position must be supplied together"
            )
        return self

    async def cli_cmd(self) -> None:
        """Initialize storage, answer once and emit resumable JSON."""
        database = Database(self.database)
        try:
            await database.initialize()
            repository = ConversationRepository(database.sessions)
            conversation_id = self.conversation_id
            position = self.expected_position or 0
            if conversation_id is None:
                conversation = await repository.create(
                    self.user_id
                )
                conversation_id = conversation.id
                position = 0
            chat = SupportChat(
                build_agent(self.llm),
                KnowledgeBase(self.knowledge),
                repository,
                self.llm,
            )
            answer = await chat.answer(
                self.user_id,
                conversation_id,
                self.question,
                expected_position=position,
            )
            result = ChatResult(
                text=answer.text,
                messages=answer.messages,
                conversation_id=conversation_id,
                next_position=position + len(answer.messages),
            )
            print(result.model_dump_json())
        finally:
            await database.close()


class Runner(BaseSettings):
    """Command-line entry point of the customer support service."""

    model_config = SettingsConfigDict(
        cli_kebab_case=True,
        cli_enforce_required=True,
    )

    ingest: CliSubCommand[Ingest]
    chat: CliSubCommand[Chat]

    def cli_cmd(self) -> None:
        """Dispatch to the selected subcommand."""
        CliApp.run_subcommand(self)


def main(args: list[str] | None = None) -> None:
    """Parse the command line, or `args` when given, and run it.

    Run it with `python -m customer_support <subcommand>`.

    Args:
        args (list[str] | None):
            Arguments to parse instead of `sys.argv`.
    """
    CliApp.run(Runner, cli_args=args)


if __name__ == "__main__":
    main()
