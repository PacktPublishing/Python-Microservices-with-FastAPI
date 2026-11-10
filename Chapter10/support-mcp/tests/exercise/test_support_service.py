import re
from uuid import UUID

import httpx2
import pytest

from fakes import FakeSupport
from support_mcp.config import SupportSettings
from support_mcp.support import (
    SupportError,
    SupportService,
    support_client,
)


async def test_ask_returns_answer_and_conversation(
    service: SupportService,
    user_id: str,
    question: str,
    reply_text: str,
    conversation_id: UUID,
) -> None:
    """The answer holds the streamed text and the new conversation."""
    answer = await service.ask(user_id, question)
    assert answer.text == reply_text, (
        "the answer must be the full text the service streamed"
    )
    assert answer.conversation_id == conversation_id, (
        "the answer must point at the conversation it created"
    )


async def test_ask_forwards_user_in_a_new_conversation(
    service: SupportService,
    fake_support: FakeSupport,
    user_id: str,
    question: str,
    first_position: int,
    conversation_id: UUID,
) -> None:
    """Both requests carry the user, and the question starts a history."""
    await service.ask(user_id, question)
    assert [call.user_id for call in fake_support.calls] == [
        user_id,
        user_id,
    ], "both requests must be made on behalf of the user"
    asked = fake_support.calls[-1]
    assert asked.conversation_id == conversation_id, (
        "the question must be asked in the created conversation"
    )
    assert asked.question == question, (
        "the question must reach the service unchanged"
    )
    assert asked.expected_position == first_position, (
        "a new conversation is asked at position zero"
    )


@pytest.mark.usefixtures("failing_support")
async def test_ask_reports_failing_service(
    service: SupportService,
    user_id: str,
    question: str,
    failure_message: str,
) -> None:
    """An error status becomes a `SupportError` naming the status."""
    with pytest.raises(
        SupportError, match=re.escape(failure_message)
    ):
        await service.ask(user_id, question)


async def test_ask_reports_timeout(
    timeout_service: SupportService,
    user_id: str,
    question: str,
    timeout_message: str,
) -> None:
    """A slow service becomes a `SupportError` saying it timed out."""
    with pytest.raises(SupportError, match=timeout_message):
        await timeout_service.ask(user_id, question)


async def test_ask_reports_unreachable_service(
    unreachable_service: SupportService,
    user_id: str,
    question: str,
    unreachable_message: str,
) -> None:
    """A refused connection becomes a `SupportError`."""
    with pytest.raises(SupportError, match=unreachable_message):
        await unreachable_service.ask(user_id, question)


async def test_support_client_uses_settings(
    support_settings: SupportSettings,
) -> None:
    """The client targets the configured URL with its timeout."""
    async with support_client(support_settings) as client:
        assert client.base_url == httpx2.URL(
            str(support_settings.url)
        ), "relative URLs must resolve against the configured URL"
        assert client.timeout == httpx2.Timeout(
            support_settings.timeout
        ), "requests must use the configured timeout"


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
