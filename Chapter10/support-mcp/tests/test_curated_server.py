from uuid import UUID

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError

from fakes import Connect, FakeSupport
from support_mcp.support import SupportAnswer


async def test_tool_returns_structured_answer(
    local_server: FastMCP,
    question: str,
    reply_text: str,
    conversation_id: UUID,
) -> None:
    """The tool returns the answer as structured content."""
    expected = SupportAnswer(
        conversation_id=conversation_id, text=reply_text
    )
    async with Client(local_server) as client:
        result = await client.call_tool(
            "ask_support", {"question": question}
        )
    assert result.structured_content == expected.model_dump(
        mode="json"
    ), "the answer must arrive as structured content"


async def test_tool_masks_unexpected_errors(
    broken_server: FastMCP, question: str, internal_detail: str
) -> None:
    """Unexpected errors reach the client without their details."""
    async with Client(broken_server) as client:
        with pytest.raises(ToolError) as error:
            await client.call_tool(
                "ask_support", {"question": question}
            )
    assert internal_detail not in str(error.value), (
        "internal error details must not leak to clients"
    )


async def test_http_forwards_token_subject(
    http_server: FastMCP,
    connect_http: Connect,
    access_token: str,
    fake_support: FakeSupport,
    question: str,
    user_id: str,
) -> None:
    """Over HTTP, the token subject is the user sent upstream."""
    async with connect_http(http_server, access_token) as client:
        await client.call_tool(
            "ask_support", {"question": question}
        )
    assert {call.user_id for call in fake_support.calls} == {
        user_id
    }, "requests must be made on behalf of the token subject"


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
