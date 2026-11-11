import os
import socket
import sys
import threading
import time
import typing as ty
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import httpx2
import jwt
import pytest
import uvicorn
from fastmcp import FastMCP
from fastmcp.client.transports import StdioTransport

from fakes import SUPPORT_URL, FakeSupport, asgi_client
from support_mcp.config import ServerSettings, SupportSettings
from support_mcp.generated import (
    build_generated_server,
    fetch_spec,
)
from support_mcp.identity import (
    ALGORITHM,
    AccessTokenVerifier,
    ForwardedIdentity,
)
from support_mcp.server import build_server
from support_mcp.support import SupportService

LOCAL_HOST = "127.0.0.1"


@pytest.fixture
def other_secret() -> str:
    """A secret the server does not know."""
    return "forged-secret-0123456789abcdef01234567"


@pytest.fixture
def spoofed_user() -> str:
    """An identity a caller claims without a token proving it."""
    return "someone-else@example.com"


@pytest.fixture
def empty_question() -> str:
    """A question the tool's schema rejects."""
    return ""


@pytest.fixture
def first_position() -> int:
    """History length of a new conversation."""
    return 0


@pytest.fixture
def failure_status() -> int:
    """Status the failing fake service answers with."""
    return 500


@pytest.fixture
def failure_message(failure_status: int) -> str:
    """Error message for a failing support service."""
    return f"Support failed ({failure_status})"


@pytest.fixture
def timeout_message() -> str:
    """Error message for a support service that is too slow."""
    return "Support timed out"


@pytest.fixture
def unreachable_message() -> str:
    """Error message for a support service that cannot be reached."""
    return "Support is unreachable"


@pytest.fixture
def unknown_caller_message() -> str:
    """Error message for a tool call without an identity."""
    return "Unknown caller"


@pytest.fixture
def curated_tools() -> set[str]:
    """Tools the curated server exposes."""
    return {"ask_support"}


@pytest.fixture
def generated_tools() -> set[str]:
    """Tools generated from the support service's routes."""
    return {"create_conversation", "ask_in_conversation"}


@pytest.fixture
def identity_header() -> str:
    """Header carrying the caller's identity to the service."""
    return "x-user-id"


@pytest.fixture
def spoofed_headers(
    identity_header: str, spoofed_user: str
) -> dict[str, str]:
    """MCP request headers claiming another user's identity."""
    return {identity_header: spoofed_user}


@pytest.fixture
def conversations_path() -> str:
    """Path of the route that creates conversations."""
    return "/conversations"


@pytest.fixture
def support_url() -> str:
    """Base URL of the support service in tests."""
    return SUPPORT_URL


@pytest.fixture
def support_timeout() -> float:
    """Request timeout configured for the support service."""
    return 5.0


@pytest.fixture
def support_settings(
    support_url: str, support_timeout: float
) -> SupportSettings:
    """Settings pointing at the fake support service."""
    return SupportSettings.model_validate(
        {"url": support_url, "timeout": support_timeout}
    )


@pytest.fixture
def failing_support(
    fake_support: FakeSupport, failure_status: int
) -> FakeSupport:
    """A fake support service whose message route fails."""
    fake_support.fail_status = failure_status
    return fake_support


@pytest.fixture
async def forwarding_client(
    fake_support: FakeSupport,
) -> AsyncIterator[httpx2.AsyncClient]:
    """Client that forwards the token subject as `X-User-Id`."""
    async with asgi_client(
        fake_support.app, auth=ForwardedIdentity()
    ) as http:
        yield http


def raising_service(error: Exception) -> SupportService:
    """Create a support service whose transport always raises.

    Args:
        error (Exception):
            The transport error to raise.

    Returns:
        SupportService:
            A service that cannot reach the support service.
    """

    def handler(_request: httpx2.Request) -> httpx2.Response:
        """Raise the configured transport error."""
        raise error

    transport = httpx2.MockTransport(handler)
    return SupportService(
        httpx2.AsyncClient(
            transport=transport, base_url=SUPPORT_URL
        )
    )


@pytest.fixture
def timeout_service() -> SupportService:
    """A support service that never answers in time."""
    return raising_service(httpx2.ReadTimeout("too slow"))


@pytest.fixture
def unreachable_service() -> SupportService:
    """A support service that refuses connections."""
    return raising_service(httpx2.ConnectError("refused"))


def signed(secret: str, claims: dict[str, ty.Any]) -> str:
    """Sign `claims` with `secret`.

    Args:
        secret (str):
            Signing secret.

        claims (dict[str, ty.Any]):
            Claims to encode.

    Returns:
        str:
            The encoded token.
    """
    return jwt.encode(claims, secret, algorithm=ALGORITHM)


@pytest.fixture
def expires_in() -> datetime:
    """Expiry of a token still valid."""
    return datetime.now(UTC) + timedelta(minutes=5)


@pytest.fixture
def refresh_token(
    secret: str, user_id: str, expires_in: datetime
) -> str:
    """A refresh token, valid but not for calling tools."""
    claims = {
        "sub": user_id,
        "type": "refresh",
        "exp": expires_in,
    }
    return signed(secret, claims)


@pytest.fixture
def expired_token(secret: str, user_id: str) -> str:
    """An access token that has expired."""
    expired = datetime.now(UTC) - timedelta(minutes=5)
    claims = {"sub": user_id, "type": "access", "exp": expired}
    return signed(secret, claims)


@pytest.fixture
def forged_token(
    other_secret: str, user_id: str, expires_in: datetime
) -> str:
    """An access token signed with the wrong secret."""
    claims = {"sub": user_id, "type": "access", "exp": expires_in}
    return signed(other_secret, claims)


@pytest.fixture
def anonymous_server(service: SupportService) -> FastMCP:
    """Curated server with neither a local user nor a token."""
    return build_server(service)


@pytest.fixture
async def failing_server(
    failing_support: FakeSupport, user_id: str
) -> AsyncIterator[FastMCP]:
    """Curated server whose support service fails."""
    async with asgi_client(failing_support.app) as http:
        yield build_server(
            SupportService(http), local_user=user_id
        )


@pytest.fixture
async def spec(client: httpx2.AsyncClient) -> dict[str, ty.Any]:
    """OpenAPI document downloaded from the fake service."""
    return await fetch_spec(client)


@pytest.fixture
def generated_server(
    spec: dict[str, ty.Any],
    forwarding_client: httpx2.AsyncClient,
    verifier: AccessTokenVerifier,
) -> FastMCP:
    """Server generated from the fake service's OpenAPI."""
    return build_generated_server(
        spec, forwarding_client, auth=verifier
    )


@pytest.fixture
def secret_env(
    monkeypatch: pytest.MonkeyPatch, secret: str
) -> str:
    """Expose the shared secret to the command line."""
    monkeypatch.setenv("SUPPORT_MCP_AUTH_JWT_SECRET_KEY", secret)
    return secret


@pytest.fixture
def run_async() -> Iterator[AsyncMock]:
    """Replace serving with a mock recording how it was started."""
    with patch.object(FastMCP, "run_async") as mocked:
        yield mocked


@pytest.fixture
def fetched_spec(
    fake_support: FakeSupport,
) -> Iterator[AsyncMock]:
    """Serve the fake OpenAPI document instead of downloading it."""
    with patch(
        "support_mcp.__main__.fetch_spec",
        return_value=fake_support.app.openapi(),
    ) as mocked:
        yield mocked


@pytest.fixture
def server_settings() -> ServerSettings:
    """Default address of the HTTP server."""
    return ServerSettings()


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
