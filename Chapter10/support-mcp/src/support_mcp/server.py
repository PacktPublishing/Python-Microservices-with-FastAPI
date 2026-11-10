from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.auth import AuthProvider
from pydantic import Field

from .identity import current_user
from .support import SupportAnswer, SupportError, SupportService

INSTRUCTIONS = (
    "Answers questions about the babysitting platform's "
    "policies: bookings, cancellations, refunds, complaints."
)

Question = Annotated[
    str,
    Field(
        min_length=1,
        description="The question, in the user's own words.",
    ),
]


def build_server(
    service: SupportService,
    *,
    local_user: str | None = None,
    auth: AuthProvider | None = None,
) -> FastMCP:
    """Create the MCP server exposing the support assistant.

    Args:
        service (SupportService):
            Client of the support service the tool calls.

        local_user (str | None):
            Caller identity for a local stdio session.

        auth (AuthProvider | None):
            Verifies bearer tokens when served over HTTP.

    Returns:
        FastMCP:
            The server with its `ask_support` tool.
    """
    mcp = FastMCP(
        "Customer Support",
        instructions=INSTRUCTIONS,
        auth=auth,
        mask_error_details=True,
    )

    @mcp.tool
    async def ask_support(question: Question) -> SupportAnswer:
        """Answer a question from the platform's documents.

        Each call starts a new conversation. Use it for policy
        questions, not for live data such as availability.
        """
        user = current_user(local_user)
        try:
            return await service.ask(user, question)
        except SupportError as error:
            raise ToolError(str(error)) from error

    return mcp
