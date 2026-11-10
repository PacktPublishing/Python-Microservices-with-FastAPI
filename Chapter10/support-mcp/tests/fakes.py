import typing as ty
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from uuid import UUID

import httpx2
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from fastmcp import Client, FastMCP
from pydantic import BaseModel, Field

SUPPORT_URL = "http://support"
UserHeader = ty.Annotated[str, Header(min_length=1)]


class Call(BaseModel):
    """One request received by the fake support service."""

    path: str
    user_id: str
    conversation_id: UUID | None = None
    question: str | None = None
    expected_position: int | None = None


class QuestionBody(BaseModel):
    """Body of the Chapter 9 message route."""

    question: str = Field(min_length=1)
    expected_position: int = Field(ge=0)


class CreatedConversation(BaseModel):
    """Response of the Chapter 9 conversation route."""

    id: UUID
    user_id: str
    created_at: datetime


class FakeSupport:
    """Stand-in for the Chapter 9 service, with the same routes."""

    def __init__(
        self, conversation_id: UUID, reply_text: str
    ) -> None:
        """Build the app and start with no calls and no failure.

        Args:
            conversation_id (UUID):
                Identifier returned for every new conversation.

            reply_text (str):
                Text streamed back for every question.
        """
        self.calls: list[Call] = []
        self.fail_status: int | None = None
        self.app = FastAPI(title="Customer Support")

        @self.app.get("/health")
        def health() -> dict[str, str]:
            """Report that the service is up."""
            return {"status": "ok"}

        @self.app.post("/knowledge/sync")
        def sync_knowledge() -> dict[str, int]:
            """Pretend to sync the knowledge base."""
            return {"added": 0}

        @self.app.post("/conversations", status_code=201)
        def create_conversation(
            x_user_id: UserHeader,
        ) -> CreatedConversation:
            """Record the owner and return a new conversation."""
            self.calls.append(
                Call(path="/conversations", user_id=x_user_id)
            )
            return CreatedConversation(
                id=conversation_id,
                user_id=x_user_id,
                created_at=datetime.now(UTC),
            )

        @self.app.post(
            "/conversations/{conversation_id}/messages"
        )
        def ask(
            conversation_id: UUID,
            body: QuestionBody,
            x_user_id: UserHeader,
        ) -> PlainTextResponse:
            """Record the question and stream the fixed reply."""
            self.calls.append(
                Call(
                    path="/messages",
                    user_id=x_user_id,
                    conversation_id=conversation_id,
                    question=body.question,
                    expected_position=body.expected_position,
                )
            )
            if self.fail_status is not None:
                raise HTTPException(self.fail_status)
            return PlainTextResponse(reply_text)


def asgi_client(
    app: FastAPI,
    auth: httpx2.Auth | None = None,
) -> httpx2.AsyncClient:
    """Create a client that calls `app` in process.

    Args:
        app (FastAPI):
            The application to call.

        auth (httpx2.Auth | None):
            Optional hook adding credentials to every request.

    Returns:
        httpx2.AsyncClient:
            A client for `app`.
    """
    return httpx2.AsyncClient(
        transport=httpx2.ASGITransport(app=app),
        base_url=SUPPORT_URL,
        auth=auth,
    )


class Connect(ty.Protocol):
    """Open an MCP client on a server, over in-process HTTP."""

    def __call__(
        self,
        server: FastMCP,
        token: str | None,
        headers: dict[str, str] | None = None,
    ) -> AbstractAsyncContextManager[Client]:
        """Connect to `server` with `token` and extra `headers`.

        Args:
            server (FastMCP):
                The server to serve in process.

            token (str | None):
                Bearer token to send, or `None` for no token.

            headers (dict[str, str] | None):
                Extra HTTP headers to send with every request.

        Returns:
            AbstractAsyncContextManager[Client]:
                A connected MCP client.
        """
        ...
