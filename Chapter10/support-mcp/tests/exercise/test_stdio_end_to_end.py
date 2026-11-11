from uuid import UUID

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from fakes import FakeSupport
from support_mcp.support import SupportAnswer


@pytest.mark.integration
async def test_stdio_server_answers_through_support_service(
    stdio_transport: StdioTransport,
    fake_support: FakeSupport,
    question: str,
    reply_text: str,
    conversation_id: UUID,
    user_id: str,
) -> None:
    """A host launches the server, which asks the running service."""
    expected = SupportAnswer(
        conversation_id=conversation_id, text=reply_text
    )
    async with Client(stdio_transport) as client:
        result = await client.call_tool(
            "ask_support", {"question": question}
        )
    assert result.structured_content == expected.model_dump(
        mode="json"
    ), "the answer must come back from the running service"
    assert {call.user_id for call in fake_support.calls} == {
        user_id
    }, "the stdio session must act as its local user"


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
