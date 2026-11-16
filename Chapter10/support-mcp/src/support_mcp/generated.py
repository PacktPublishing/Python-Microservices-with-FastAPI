import typing as ty

import httpx2
from fastmcp import FastMCP
from fastmcp.server.auth import AuthProvider
from fastmcp.server.providers.openapi import (
    MCPType,
    OpenAPIResource,
    OpenAPIResourceTemplate,
    OpenAPITool,
    RouteMap,
)
from fastmcp.utilities.openapi import HTTPRoute

EXCLUDED = RouteMap(
    pattern=r"^/(health|knowledge/sync)$",
    mcp_type=MCPType.EXCLUDE,
)
NAMES = {
    "create_conversation_conversations_post": (
        "create_conversation"
    ),
    "ask_conversations__conversation_id__messages_post": (
        "ask_in_conversation"
    ),
}
IDENTITY_HEADER = "x-user-id"
Component = (
    OpenAPITool | OpenAPIResource | OpenAPIResourceTemplate
)


async def fetch_spec(
    client: httpx2.AsyncClient,
) -> dict[str, ty.Any]:
    """Download the OpenAPI document of the support service.

    Args:
        client (httpx2.AsyncClient):
            Client configured for the support service.

    Returns:
        dict[str, ty.Any]:
            The parsed OpenAPI document.
    """
    response = await client.get("/openapi.json")
    response.raise_for_status()
    spec: dict[str, ty.Any] = response.json()
    return spec


def hide_identity(
    route: HTTPRoute,
    component: Component,
) -> None:
    """Remove the identity header from a generated tool's input.

    Args:
        route (HTTPRoute):
            The route the component was generated from.

        component (Component):
            The generated component, changed in place.
    """
    takes_identity = any(
        param.location == "header"
        and param.name.lower() == IDENTITY_HEADER
        for param in route.parameters
    )
    if not takes_identity:
        return
    if not isinstance(component, OpenAPITool):
        return
    schema = component.parameters
    schema["properties"].pop(IDENTITY_HEADER)
    if IDENTITY_HEADER in schema["required"]:
        schema["required"].remove(IDENTITY_HEADER)


def build_generated_server(
    spec: dict[str, ty.Any],
    client: httpx2.AsyncClient,
    auth: AuthProvider | None = None,
) -> FastMCP:
    """Generate an MCP server from the support service's OpenAPI.

    Args:
        spec (dict[str, ty.Any]):
            OpenAPI document of the support service.

        client (httpx2.AsyncClient):
            Client the generated tools send their requests with.

        auth (AuthProvider | None):
            Verifies bearer tokens when served over HTTP.

    Returns:
        FastMCP:
            One tool per remaining route.
    """
    return FastMCP.from_openapi(
        spec,
        client=client,
        name="Customer Support (generated)",
        route_maps=[EXCLUDED],
        mcp_names=NAMES,
        mcp_component_fn=hide_identity,
        auth=auth,
        mask_error_details=True,
    )
