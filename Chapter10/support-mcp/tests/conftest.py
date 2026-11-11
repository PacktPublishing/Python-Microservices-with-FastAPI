import typing as ty
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from unittest.mock import patch
from uuid import UUID

import httpx2
import pytest
from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from pydantic import SecretStr

from fakes import Connect, FakeSupport, asgi_client
from support_mcp.config import AuthSettings
from support_mcp.identity import (
    AccessTokenVerifier,
    build_verifier,
    create_token,
)
from support_mcp.server import build_server
from support_mcp.support import SupportService

MCP_URL = "http://mcp/mcp"


@pytest.fixture
def user_id() -> str:
    """The user asking questions."""
    return "parent@example.com"


@pytest.fixture
def question() -> str:
    """A support question."""
    return "Can I cancel a booking for free?"


@pytest.fixture
def reply_text() -> str:
    """The answer the fake support service returns."""
    return "Yes, up to 24 hours before the booking starts."


@pytest.fixture
def conversation_id() -> UUID:
    """Identifier of the conversation the fake service creates."""
    return UUID("6f1c2d9e-8a4b-4c3d-9e2f-1a2b3c4d5e6f")


@pytest.fixture
def internal_detail() -> str:
    """Text of an unexpected error that must not reach clients."""
    return "database password is hunter2"


@pytest.fixture
def fake_support(
    conversation_id: UUID, reply_text: str
) -> FakeSupport:
    """A healthy fake support service."""
    return FakeSupport(conversation_id, reply_text)


@pytest.fixture
async def client(
    fake_support: FakeSupport,
) -> AsyncIterator[httpx2.AsyncClient]:
    """Client of the fake support service."""
    async with asgi_client(fake_support.app) as http:
        yield http


@pytest.fixture
def service(client: httpx2.AsyncClient) -> SupportService:
    """Support service client wired to the fake service."""
    return SupportService(client)


@pytest.fixture
def local_server(
    service: SupportService, user_id: str
) -> FastMCP:
    """Curated server as served over stdio, for a local user."""
    return build_server(service, local_user=user_id)


@pytest.fixture
def broken_service(
    service: SupportService, internal_detail: str
) -> Iterator[SupportService]:
    """A support service that fails with an unexpected error."""
    with patch.object(
        service, "ask", side_effect=RuntimeError(internal_detail)
    ):
        yield service


@pytest.fixture
def broken_server(
    broken_service: SupportService, user_id: str
) -> FastMCP:
    """Curated server whose service raises an unexpected error."""
    return build_server(broken_service, local_user=user_id)


@pytest.fixture
def secret() -> str:
    """Shared secret, long enough for HS256."""
    return "test-secret-0123456789abcdef0123456789"


@pytest.fixture
def auth_settings(secret: str) -> AuthSettings:
    """Authentication settings holding the shared secret."""
    return AuthSettings(jwt_secret_key=SecretStr(secret))


@pytest.fixture
def verifier(auth_settings: AuthSettings) -> AccessTokenVerifier:
    """Verifier of Chapter 8 access tokens."""
    return build_verifier(auth_settings)


@pytest.fixture
def access_token(
    auth_settings: AuthSettings, user_id: str
) -> str:
    """A valid access token for the user."""
    return create_token(auth_settings, user_id)


@pytest.fixture
def http_server(
    service: SupportService, verifier: AccessTokenVerifier
) -> FastMCP:
    """Curated server as served over HTTP, with authentication."""
    return build_server(service, auth=verifier)


@pytest.fixture
def connect_http() -> Connect:
    """Connect a client to a server over in-process HTTP."""

    @asynccontextmanager
    async def connect(
        server: FastMCP,
        token: str | None,
        headers: dict[str, str] | None = None,
    ) -> AsyncIterator[Client]:
        """Serve `server` in process and connect with `token`."""
        app = server.http_app(path="/mcp")

        def factory(**kwargs: ty.Any) -> httpx2.AsyncClient:
            """Send the client's requests straight to `app`."""
            transport = httpx2.ASGITransport(app=app)
            return httpx2.AsyncClient(
                transport=transport, **kwargs
            )

        transport = StreamableHttpTransport(
            MCP_URL,
            headers=headers,
            auth=token,
            httpx_client_factory=factory,
        )
        async with app.router.lifespan_context(app):
            async with Client(transport) as mcp_client:
                yield mcp_client

    return connect
