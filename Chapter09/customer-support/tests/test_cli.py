import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest
from pydantic import ValidationError
from pydantic_ai.messages import ModelMessagesTypeAdapter

from customer_support.__main__ import Chat, ChatResult, main
from customer_support.config import KnowledgeSettings
from customer_support.conversations import (
    ConversationConflict,
    ConversationNotFound,
    ConversationRepository,
    Database,
)
from customer_support.knowledge import KnowledgeBase


def test_ingest_command_syncs_the_folder(
    ingestion_environment: KnowledgeSettings,
    cancellation_source: str,
    retrieval_query: str,
) -> None:
    """Run `ingest`, then search the knowledge base it stored."""
    main(["ingest"])
    knowledge_base = KnowledgeBase(ingestion_environment)
    best = knowledge_base.search(retrieval_query, limit=1)[0]
    assert best.source == cancellation_source, (
        "The synced cancellation policy must be searchable."
    )


def test_ingest_flag_overrides_environment(
    ingestion_environment: KnowledgeSettings,
    cli_storage_path: Path,
    sample_sources: list[str],
) -> None:
    """Check `--storage-path` wins over the environment variable."""
    main(["ingest", "--storage-path", str(cli_storage_path)])
    settings = ingestion_environment.model_copy(
        update={"storage_path": cli_storage_path}
    )
    report = KnowledgeBase(settings).sync()
    assert report.unchanged == sample_sources, (
        "The flag's folder must hold the synced documents."
    )
    assert not ingestion_environment.storage_path.exists(), (
        "The environment's folder must not be created."
    )


def test_chat_creates_and_resumes(
    cli_chat_args: list[str],
    cli_chat_environment: Database,
    cli_close_spy: AsyncMock,
    capsys: pytest.CaptureFixture[str],
    user_id: str,
    reply_text: str,
) -> None:
    """Separate CLI invocations persist history and report resume values."""
    main(cli_chat_args)
    first = ChatResult.model_validate_json(
        capsys.readouterr().out
    )
    assert first.text == reply_text, (
        "CLI output must include the generated answer."
    )
    assert first.next_position == len(first.messages), (
        "The initial position must count all saved messages."
    )
    main(
        cli_chat_args
        + [
            "--conversation-id",
            str(first.conversation_id),
            "--expected-position",
            str(first.next_position),
        ]
    )
    second = ChatResult.model_validate_json(
        capsys.readouterr().out
    )
    assert second.conversation_id == first.conversation_id, (
        "Resume must retain the conversation ID."
    )
    assert second.next_position == first.next_position + len(
        second.messages
    ), "Report the committed next position."
    repository = ConversationRepository(
        cli_chat_environment.sessions
    )
    loaded = asyncio.run(
        repository.load(user_id, first.conversation_id)
    )
    asyncio.run(cli_chat_environment.close())
    assert loaded is not None, (
        "The CLI-created conversation must persist on disk."
    )
    assert ModelMessagesTypeAdapter.dump_json(
        loaded.messages
    ) == ModelMessagesTypeAdapter.dump_json(
        first.messages + second.messages
    ), "Persist both complete turns without duplicating history."
    assert cli_close_spy.await_count >= 2, (
        "Each CLI invocation must close the database."
    )


@pytest.mark.usefixtures("cli_chat_environment")
def test_chat_retry_does_not_duplicate(
    cli_chat_args: list[str],
    capsys: pytest.CaptureFixture[str],
    search_stub: Mock,
) -> None:
    """A repeated resume request retains its original expected position."""
    main(cli_chat_args)
    first = ChatResult.model_validate_json(
        capsys.readouterr().out
    )
    args = cli_chat_args + [
        "--conversation-id",
        str(first.conversation_id),
        "--expected-position",
        str(first.next_position),
    ]
    main(args)
    capsys.readouterr()
    calls = search_stub.search.call_count
    with pytest.raises(ConversationConflict):
        main(args)
    assert search_stub.search.call_count == calls, (
        "A committed retry must not trigger another retrieval."
    )
    assert not capsys.readouterr().out, (
        "A failed retry must not print a successful answer."
    )


@pytest.mark.usefixtures("cli_chat_environment")
def test_chat_hides_foreign_and_missing_ids(
    cli_chat_args: list[str],
    capsys: pytest.CaptureFixture[str],
    other_user_id: str,
    retrieval_query: str,
    missing_id: UUID,
    search_stub: Mock,
) -> None:
    """The CLI uses repository ownership checks for every resumed turn."""
    main(cli_chat_args)
    first = ChatResult.model_validate_json(
        capsys.readouterr().out
    )
    search_stub.search.reset_mock()
    for identifier in (first.conversation_id, missing_id):
        with pytest.raises(ConversationNotFound):
            main(
                [
                    "chat",
                    "--user-id",
                    other_user_id,
                    "--question",
                    retrieval_query,
                    "--conversation-id",
                    str(identifier),
                    "--expected-position",
                    str(first.next_position),
                ]
            )
    search_stub.search.assert_not_called()


def test_chat_requires_resume_position(
    user_id: str, retrieval_query: str, missing_id: UUID
) -> None:
    """A resume identifier without a position is rejected before execution."""
    with pytest.raises(ValidationError):
        Chat(
            user_id=user_id,
            question=retrieval_query,
            conversation_id=missing_id,
        )


def test_chat_rejects_position_without_conversation(
    user_id: str, retrieval_query: str
) -> None:
    """An expected position only has meaning for a resumed conversation."""
    with pytest.raises(ValidationError):
        Chat(
            user_id=user_id,
            question=retrieval_query,
            expected_position=0,
        )


@pytest.mark.parametrize(
    "missing_flag", ["--user-id", "--question"]
)
def test_chat_requires_identity_and_question(
    cli_chat_args: list[str], missing_flag: str
) -> None:
    """Missing required command flags fail in the CLI parser."""
    args = cli_chat_args.copy()
    index = args.index(missing_flag)
    del args[index : index + 2]
    with pytest.raises(SystemExit):
        main(args)


def test_chat_closes_database_on_initialization_failure(
    cli_chat_args: list[str],
    cli_initialization_failure: AsyncMock,
    cli_close_spy: AsyncMock,
) -> None:
    """Cleanup runs even if missing tables cannot be initialized."""
    with pytest.raises(RuntimeError):
        main(cli_chat_args)
    cli_initialization_failure.assert_awaited_once()
    cli_close_spy.assert_awaited_once()


def test_chat_closes_database_on_model_failure(
    cli_chat_args: list[str],
    cli_model_failure: Mock,
    cli_close_spy: AsyncMock,
) -> None:
    """Failed model setup cannot leave database connections open."""
    with pytest.raises(RuntimeError):
        main(cli_chat_args)
    cli_model_failure.assert_called_once()
    cli_close_spy.assert_awaited_once()


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
