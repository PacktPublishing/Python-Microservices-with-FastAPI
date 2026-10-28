import asyncio
from uuid import UUID

import pytest
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
)

from customer_support.config import DatabaseSettings
from customer_support.conversations import (
    ConversationConflict,
    ConversationNotFound,
    ConversationRepository,
    Database,
)


async def test_create_and_list_owned_conversations(
    repository: ConversationRepository,
    user_id: str,
    other_user_id: str,
) -> None:
    """Listing never includes another user's conversation."""
    own = await repository.create(user_id)
    await repository.create(other_user_id)
    assert await repository.list_conversations(user_id) == [
        own
    ], "List must filter by owner."
    loaded = await repository.load(user_id, own.id)
    assert loaded is not None and not loaded.messages, (
        "A new conversation has an empty history."
    )


async def test_missing_and_foreign_conversations_are_hidden(
    repository: ConversationRepository,
    user_id: str,
    other_user_id: str,
    missing_id: UUID,
    saved_messages: list[ModelMessage],
) -> None:
    """Loads and appends hide whether a foreign conversation exists."""
    foreign = await repository.create(other_user_id)
    for identifier in (foreign.id, missing_id):
        assert (
            await repository.load(user_id, identifier) is None
        ), (
            "Foreign and missing conversations must both be invisible."
        )
        with pytest.raises(ConversationNotFound):
            await repository.append(
                user_id,
                identifier,
                saved_messages,
                expected_position=0,
            )
    loaded = await repository.load(other_user_id, foreign.id)
    assert loaded is not None and not loaded.messages, (
        "A denied append must not change another user's data."
    )


async def test_history_survives_restart(
    repository: ConversationRepository,
    database: Database,
    database_settings: DatabaseSettings,
    user_id: str,
    saved_messages: list[ModelMessage],
) -> None:
    """Dispose the engine and recover typed messages from disk."""
    own = await repository.create(user_id)
    await repository.append(
        user_id, own.id, saved_messages, expected_position=0
    )
    await database.close()
    reopened = Database(database_settings)
    try:
        await reopened.initialize()
        loaded = await ConversationRepository(
            reopened.sessions
        ).load(user_id, own.id)
        assert loaded is not None, (
            "The owner must resume the persisted conversation."
        )
        assert ModelMessagesTypeAdapter.dump_json(
            loaded.messages
        ) == ModelMessagesTypeAdapter.dump_json(saved_messages), (
            "Message types, order and contents must survive serialization."
        )
    finally:
        await reopened.close()


async def test_stale_append_is_not_duplicated(
    repository: ConversationRepository,
    user_id: str,
    saved_messages: list[ModelMessage],
) -> None:
    """Retrying the same append cannot duplicate a committed run."""
    own = await repository.create(user_id)
    await repository.append(
        user_id, own.id, saved_messages, expected_position=0
    )
    with pytest.raises(ConversationConflict):
        await repository.append(
            user_id, own.id, saved_messages, expected_position=0
        )
    loaded = await repository.load(user_id, own.id)
    assert (
        loaded is not None and loaded.messages == saved_messages
    ), "Stale writes must leave the successful history unchanged."


async def test_concurrent_append_has_one_winner(
    repository: ConversationRepository,
    user_id: str,
    saved_messages: list[ModelMessage],
) -> None:
    """Database compare-and-swap rejects simultaneous stale runs."""
    own = await repository.create(user_id)
    outcomes = await asyncio.gather(
        repository.append(
            user_id, own.id, saved_messages, expected_position=0
        ),
        repository.append(
            user_id, own.id, saved_messages, expected_position=0
        ),
        return_exceptions=True,
    )
    assert (
        sum(
            isinstance(outcome, ConversationConflict)
            for outcome in outcomes
        )
        == 1
    ), "Exactly one concurrent append must be rejected."
    loaded = await repository.load(user_id, own.id)
    assert (
        loaded is not None and loaded.messages == saved_messages
    ), "The winner must persist exactly one batch."


async def test_empty_append_preserves_history(
    repository: ConversationRepository, user_id: str
) -> None:
    """An empty batch does not create message rows."""
    own = await repository.create(user_id)
    await repository.append(
        user_id, own.id, [], expected_position=0
    )
    loaded = await repository.load(user_id, own.id)
    assert loaded is not None and not loaded.messages, (
        "An empty append must preserve an empty history."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
