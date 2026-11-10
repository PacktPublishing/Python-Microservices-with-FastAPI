import os
import socket
import sys
import threading
import time
import typing as ty
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from unittest.mock import patch
from uuid import UUID

import httpx2
import pytest
import uvicorn
from fastmcp import Client, FastMCP
from fastmcp.client.transports import (
    StdioTransport,
    StreamableHttpTransport,
)
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
LOCAL_HOST = "127.0.0.1"


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


def free_port() -> int:
    """Ask the operating system for an unused local port.

    Returns:
        int:
            A port nothing listens on.
    """
    with socket.socket() as sock:
        sock.bind((LOCAL_HOST, 0))
        port: int = sock.getsockname()[1]
        return port


@pytest.fixture
def running_support(fake_support: FakeSupport) -> Iterator[str]:
    """Serve the fake support service on a real local port."""
    port = free_port()
    config = uvicorn.Config(
        fake_support.app,
        host=LOCAL_HOST,
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    yield f"http://{LOCAL_HOST}:{port}"
    server.should_exit = True
    thread.join()


@pytest.fixture
def stdio_transport(
    running_support: str, user_id: str
) -> StdioTransport:
    """Launch the server as a host application would, over stdio."""
    env = {
        **os.environ,
        "SUPPORT_MCP_SUPPORT_URL": running_support,
    }
    return StdioTransport(
        command=sys.executable,
        args=[
            "-m",
            "support_mcp",
            "stdio",
            "--local-user",
            user_id,
        ],
        env=env,
    )
