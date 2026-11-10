from unittest.mock import AsyncMock

import pytest

from support_mcp.__main__ import main
from support_mcp.config import ServerSettings
from support_mcp.identity import AccessTokenVerifier


def test_stdio_serves_over_stdio(
    run_async: AsyncMock, user_id: str
) -> None:
    """`stdio` serves the curated server on standard streams."""
    main(["stdio", "--local-user", user_id])
    run_async.assert_awaited_once_with(
        transport="stdio", show_banner=False
    )


@pytest.mark.usefixtures("secret_env")
def test_http_serves_over_http(
    run_async: AsyncMock,
    server_settings: ServerSettings,
) -> None:
    """`http` serves the curated server on the configured port."""
    main(["http"])
    run_async.assert_awaited_once_with(
        transport="http",
        host=str(server_settings.host),
        port=server_settings.port,
    )


@pytest.mark.usefixtures("secret_env")
def test_generated_serves_downloaded_spec(
    run_async: AsyncMock,
    fetched_spec: AsyncMock,
    server_settings: ServerSettings,
) -> None:
    """`generated` downloads the OpenAPI document, then serves it."""
    main(["generated"])
    fetched_spec.assert_awaited_once()
    run_async.assert_awaited_once_with(
        transport="http",
        host=str(server_settings.host),
        port=server_settings.port,
    )


@pytest.mark.usefixtures("secret_env")
async def test_token_prints_access_token(
    capsys: pytest.CaptureFixture[str],
    verifier: AccessTokenVerifier,
    user_id: str,
) -> None:
    """`token` prints an access token the server accepts."""
    main(["token", "--subject", user_id])
    token = capsys.readouterr().out.strip()
    access = await verifier.verify_token(token)
    assert access is not None, (
        "the printed token must be accepted"
    )
    assert access.subject == user_id, (
        "the token must identify the requested user"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
