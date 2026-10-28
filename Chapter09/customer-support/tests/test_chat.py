from unittest.mock import Mock
from uuid import UUID

import pytest
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    SystemPromptPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from customer_support.chat import SupportChat
from customer_support.conversations import (
    ConversationConflict,
    ConversationNotFound,
    ConversationRepository,
)
from customer_support.knowledge import Chunk


async def test_answer_uses_retrieval_and_cites_source(
    chat: SupportChat,
    user_id: str,
    retrieval_query: str,
    scripted_model: FunctionModel,
    search_stub: Mock,
    reply_text: str,
    cancellation_source: str,
) -> None:
    """The scripted model receives real tool results before answering."""
    conversation = await chat.repository.create(user_id)
    with chat.agent.override(model=scripted_model):
        answer = await chat.answer(
            user_id,
            conversation.id,
            retrieval_query,
            expected_position=0,
        )
    search_stub.search.assert_called_once_with(
        retrieval_query, limit=chat.settings.retrieval_limit
    )
    assert answer.text == reply_text, (
        "The scripted model must cite the actual retrieved passage."
    )
    assert cancellation_source in answer.text, (
        "The citation must remain visible to the user."
    )
    loaded = await chat.repository.load(user_id, conversation.id)
    assert loaded is not None, (
        "The completed turn must remain available."
    )
    assert ModelMessagesTypeAdapter.dump_json(
        loaded.messages
    ) == ModelMessagesTypeAdapter.dump_json(answer.messages), (
        "Persist the exact complete new message batch."
    )
    returns = [
        part
        for message in loaded.messages
        if isinstance(message, ModelRequest)
        for part in message.parts
        if isinstance(part, ToolReturnPart)
    ]
    content = returns[0].content
    assert isinstance(content, list), (
        "Retrieval returns a list of passages."
    )
    chunks = [Chunk.model_validate(chunk) for chunk in content]
    assert chunks == search_stub.search.return_value, (
        "Stored evidence must include original text and source paths."
    )


async def test_follow_up_resends_history(
    chat: SupportChat,
    user_id: str,
    retrieval_query: str,
    test_model: TestModel,
) -> None:
    """Two turns preserve order and append only the new messages."""
    conversation = await chat.repository.create(user_id)
    with chat.agent.override(model=test_model):
        first = await chat.answer(
            user_id,
            conversation.id,
            retrieval_query,
            expected_position=0,
        )
        second = await chat.answer(
            user_id,
            conversation.id,
            retrieval_query,
            expected_position=len(first.messages),
        )
    loaded = await chat.repository.load(user_id, conversation.id)
    assert loaded is not None, (
        "An owned conversation must load after both turns."
    )
    assert ModelMessagesTypeAdapter.dump_json(
        loaded.messages
    ) == ModelMessagesTypeAdapter.dump_json(
        first.messages + second.messages
    ), "The second run must not append the earlier history again."


async def test_foreign_conversation_never_calls_model(
    chat: SupportChat,
    repository: ConversationRepository,
    user_id: str,
    other_user_id: str,
    missing_id: UUID,
    retrieval_query: str,
    search_stub: Mock,
) -> None:
    """Ownership is checked before any inference or retrieval occurs."""
    foreign = await repository.create(other_user_id)
    for identifier in (foreign.id, missing_id):
        with pytest.raises(ConversationNotFound):
            await chat.answer(
                user_id,
                identifier,
                retrieval_query,
                expected_position=0,
            )
    search_stub.search.assert_not_called()


async def test_empty_retrieval_reaches_model(
    chat: SupportChat,
    user_id: str,
    retrieval_query: str,
    scripted_model: FunctionModel,
    search_stub: Mock,
    fallback_text: str,
) -> None:
    """An empty search is visible to the model without invented evidence."""
    search_stub.search.return_value = []
    conversation = await chat.repository.create(user_id)
    with chat.agent.override(model=scripted_model):
        answer = await chat.answer(
            user_id,
            conversation.id,
            retrieval_query,
            expected_position=0,
        )
    assert answer.text == fallback_text, (
        "Return the scripted model's explicit lack-of-evidence answer."
    )


async def test_request_limit_leaves_history_unchanged(
    chat: SupportChat,
    user_id: str,
    retrieval_query: str,
    looping_model: FunctionModel,
    search_stub: Mock,
) -> None:
    """Stop an endless tool loop without committing a partial turn."""
    conversation = await chat.repository.create(user_id)
    with (
        chat.agent.override(model=looping_model),
        pytest.raises(UsageLimitExceeded),
    ):
        await chat.answer(
            user_id,
            conversation.id,
            retrieval_query,
            expected_position=0,
        )
    loaded = await chat.repository.load(user_id, conversation.id)
    assert loaded is not None and not loaded.messages, (
        "A failed run must not persist an incomplete tool exchange."
    )
    assert (
        search_stub.search.call_count
        == chat.settings.request_limit
    ), "The loop must stop at the configured request budget."


async def test_model_receives_restored_history(
    chat: SupportChat,
    user_id: str,
    retrieval_query: str,
    history_model: FunctionModel,
    model_calls: list[list[ModelMessage]],
) -> None:
    """Inspect the model boundary to prove saved history is resent."""
    conversation = await chat.repository.create(user_id)
    with chat.agent.override(model=history_model):
        first = await chat.answer(
            user_id,
            conversation.id,
            retrieval_query,
            expected_position=0,
        )
        await chat.answer(
            user_id,
            conversation.id,
            retrieval_query,
            expected_position=len(first.messages),
        )
    assert ModelMessagesTypeAdapter.dump_json(
        model_calls[-1][: len(first.messages)]
    ) == ModelMessagesTypeAdapter.dump_json(first.messages), (
        "The second inference must receive the persisted first turn as its prefix."
    )


async def test_retried_answer_does_not_append_again(
    chat: SupportChat,
    user_id: str,
    retrieval_query: str,
    history_model: FunctionModel,
    model_calls: list[list[ModelMessage]],
) -> None:
    """Retrying a committed request with its original version is safe."""
    conversation = await chat.repository.create(user_id)
    with chat.agent.override(model=history_model):
        first = await chat.answer(
            user_id,
            conversation.id,
            retrieval_query,
            expected_position=0,
        )
        calls_before_retry = len(model_calls)
        with pytest.raises(ConversationConflict):
            await chat.answer(
                user_id,
                conversation.id,
                retrieval_query,
                expected_position=0,
            )
    assert len(model_calls) == calls_before_retry, (
        "A committed retry must fail before another model request."
    )
    loaded = await chat.repository.load(user_id, conversation.id)
    assert (
        loaded is not None and loaded.messages == first.messages
    ), (
        "The retried operation must not duplicate the persisted turn."
    )


async def test_required_prompt_reaches_model(
    chat: SupportChat,
    user_id: str,
    retrieval_query: str,
    history_model: FunctionModel,
    model_calls: list[list[ModelMessage]],
    required_instructions: list[str],
) -> None:
    """Protect safety and grounding instructions at the model boundary."""
    conversation = await chat.repository.create(user_id)
    with chat.agent.override(model=history_model):
        await chat.answer(
            user_id,
            conversation.id,
            retrieval_query,
            expected_position=0,
        )
    prompts = [
        part.content
        for message in model_calls[0]
        if isinstance(message, ModelRequest)
        for part in message.parts
        if isinstance(part, SystemPromptPart)
    ]
    assert all(
        instruction in " ".join(prompts)
        for instruction in required_instructions
    ), (
        "Persona, grounding, citations, fallback and untrusted-document rules must reach the model."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
