import typing as ty
from unittest.mock import create_autospec
from uuid import UUID

import httpx2
import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.providers.openapi import (
    OpenAPIResource,
    OpenAPITool,
)
from fastmcp.utilities.openapi import HTTPRoute, ParameterInfo

from fakes import Connect, FakeSupport
from support_mcp.generated import (
    build_generated_server,
    hide_identity,
)


def test_spec_describes_support_routes(
    spec: dict[str, ty.Any],
    conversations_path: str,
) -> None:
    """The downloaded document describes the service's routes."""
    assert conversations_path in spec["paths"], (
        "the OpenAPI document must list the conversation route"
    )


async def test_generated_tools_skip_operational_routes(
    generated_server: FastMCP,
    connect_http: Connect,
    access_token: str,
    generated_tools: set[str],
) -> None:
    """Health and sync routes are excluded, the rest renamed."""
    async with connect_http(
        generated_server,
        access_token,
    ) as client:
        tools = await client.list_tools()
    assert {tool.name for tool in tools} == generated_tools, (
        "only the conversation routes must become tools"
    )


async def test_generated_tools_hide_identity_header(
    generated_server: FastMCP,
    connect_http: Connect,
    access_token: str,
    identity_header: str,
) -> None:
    """No generated tool lets the model choose the user."""
    async with connect_http(
        generated_server,
        access_token,
    ) as client:
        tools = await client.list_tools()
    for tool in tools:
        assert identity_header not in tool.input_schema.get(
            "properties",
            {},
        ), f"{tool.name} must not take the user as an argument"


async def test_generated_tools_act_as_token_subject(
    generated_server: FastMCP,
    connect_http: Connect,
    access_token: str,
    fake_support: FakeSupport,
    conversation_id: UUID,
    question: str,
    first_position: int,
    reply_text: str,
    user_id: str,
) -> None:
    """Generated tools call the service on behalf of the token subject."""
    async with connect_http(
        generated_server,
        access_token,
    ) as client:
        created = await client.call_tool(
            "create_conversation",
            {},
        )
        answer = await client.call_tool(
            "ask_in_conversation",
            {
                "conversation_id": str(conversation_id),
                "question": question,
                "expected_position": first_position,
            },
        )
    assert created.structured_content is not None, (
        "the created conversation must be returned"
    )
    assert created.structured_content["id"] == str(
        conversation_id,
    ), "the tool must return the conversation the service created"
    assert answer.content[0].text == reply_text, (  # type: ignore[union-attr]
        "the tool must return the service's text answer"
    )
    assert {call.user_id for call in fake_support.calls} == {
        user_id,
    }, "requests must be made on behalf of the token subject"


async def test_generated_tools_ignore_spoofed_identity(
    generated_server: FastMCP,
    connect_http: Connect,
    access_token: str,
    spoofed_headers: dict[str, str],
    fake_support: FakeSupport,
    user_id: str,
) -> None:
    """A signed-in caller cannot claim another user with a header."""
    async with connect_http(
        generated_server,
        access_token,
        spoofed_headers,
    ) as client:
        await client.call_tool("create_conversation", {})
    assert {call.user_id for call in fake_support.calls} == {
        user_id,
    }, "the token subject must replace a spoofed X-User-Id"


async def test_generated_tools_need_a_token_subject(
    spec: dict[str, ty.Any],
    forwarding_client: httpx2.AsyncClient,
    fake_support: FakeSupport,
) -> None:
    """Without a token there is no user, and the service refuses."""
    server = build_generated_server(spec, forwarding_client)
    async with Client(server) as client:
        with pytest.raises(ToolError):
            await client.call_tool("create_conversation", {})
    assert fake_support.calls == [], (
        "no conversation may be created without a user"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])


def identity_route(identity_header: str) -> HTTPRoute:
    """A route that reads the identity header."""
    header = ParameterInfo(
        name=identity_header,
        location="header",
        schema={},
    )
    return HTTPRoute(
        path="/x",
        method="POST",
        parameters=[header],
    )


def test_hide_identity_skips_routes_without_header(
    identity_header: str,
) -> None:
    """A route without the header keeps its tool unchanged."""
    schema = {"properties": {identity_header: {}}, "required": []}
    tool = create_autospec(OpenAPITool, instance=True)
    tool.parameters = schema
    hide_identity(HTTPRoute(path="/x", method="GET"), tool)
    assert identity_header in schema["properties"], (
        "routes without the header must not be changed"
    )


def test_hide_identity_skips_resources(
    identity_header: str,
) -> None:
    """Resources have no input schema to edit."""
    resource = create_autospec(OpenAPIResource, instance=True)
    hide_identity(identity_route(identity_header), resource)
    assert not resource.method_calls, (
        "resources must be left untouched"
    )
