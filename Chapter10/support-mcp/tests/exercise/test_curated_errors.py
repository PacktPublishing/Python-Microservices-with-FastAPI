import re

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from mcp.shared.exceptions import MCPError

from fakes import Connect, FakeSupport


async def test_server_lists_curated_tool(
    local_server: FastMCP, curated_tools: set[str]
) -> None:
    """The server exposes exactly the curated tool."""
    async with Client(local_server) as client:
        tools = await client.list_tools()
    assert {tool.name for tool in tools} == curated_tools, (
        "only the curated tool must be exposed"
    )


async def test_tool_requires_a_question(
    local_server: FastMCP,
) -> None:
    """The question is required and cannot be empty."""
    async with Client(local_server) as client:
        (tool,) = await client.list_tools()
    schema = tool.input_schema["properties"]["question"]
    assert tool.input_schema["required"] == ["question"], (
        "the question must be a required argument"
    )
    assert schema["minLength"] == 1, (
        "an empty question must be rejected by the schema"
    )


async def test_tool_rejects_an_empty_question(
    local_server: FastMCP,
    fake_support: FakeSupport,
    empty_question: str,
) -> None:
    """The server validates arguments before the tool runs."""
    async with Client(local_server) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "ask_support", {"question": empty_question}
            )
    assert fake_support.calls == [], (
        "an invalid question must not reach the support service"
    )


async def test_tool_reports_support_failure(
    failing_server: FastMCP, question: str, failure_message: str
) -> None:
    """A failing support service becomes a readable tool error."""
    async with Client(failing_server) as client:
        with pytest.raises(
            ToolError, match=re.escape(failure_message)
        ):
            await client.call_tool(
                "ask_support", {"question": question}
            )


async def test_tool_refuses_unknown_caller(
    anonymous_server: FastMCP,
    fake_support: FakeSupport,
    question: str,
    unknown_caller_message: str,
) -> None:
    """Without an identity, no request reaches the service."""
    async with Client(anonymous_server) as client:
        with pytest.raises(
            ToolError, match=unknown_caller_message
        ):
            await client.call_tool(
                "ask_support", {"question": question}
            )
    assert fake_support.calls == [], (
        "an anonymous call must not reach the support service"
    )


@pytest.mark.parametrize(
    "token_fixture", ["refresh_token", "forged_token"]
)
async def test_http_rejects_invalid_tokens(
    http_server: FastMCP,
    connect_http: Connect,
    request: pytest.FixtureRequest,
    token_fixture: str,
) -> None:
    """Refresh and forged tokens cannot open a session."""
    token = request.getfixturevalue(token_fixture)
    with pytest.raises(ExceptionGroup) as error:
        async with connect_http(http_server, token) as client:
            await client.list_tools()
    assert error.group_contains(MCPError), (
        "the server must refuse the session"
    )


async def test_http_requires_a_token(
    http_server: FastMCP, connect_http: Connect
) -> None:
    """A client without a token cannot open a session."""
    with pytest.raises(ExceptionGroup) as error:
        async with connect_http(http_server, None) as client:
            await client.list_tools()
    assert error.group_contains(MCPError), (
        "the server must refuse the session"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
