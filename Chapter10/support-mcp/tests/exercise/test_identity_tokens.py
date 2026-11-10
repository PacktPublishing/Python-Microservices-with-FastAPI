import httpx2
import pytest
from fastmcp.exceptions import ToolError

from fakes import FakeSupport
from support_mcp.identity import AccessTokenVerifier, current_user


async def test_verifier_accepts_access_token(
    verifier: AccessTokenVerifier, access_token: str, user_id: str
) -> None:
    """A signed access token is accepted and identifies the user."""
    access = await verifier.verify_token(access_token)
    assert access is not None, (
        "a valid access token must be accepted"
    )
    assert access.subject == user_id, (
        "the token subject must be the user it was issued for"
    )


async def test_verifier_rejects_refresh_token(
    verifier: AccessTokenVerifier, refresh_token: str
) -> None:
    """A refresh token is valid but cannot call tools."""
    assert await verifier.verify_token(refresh_token) is None, (
        "only access tokens may call tools"
    )


async def test_verifier_rejects_expired_token(
    verifier: AccessTokenVerifier, expired_token: str
) -> None:
    """An expired access token is rejected."""
    assert await verifier.verify_token(expired_token) is None, (
        "an expired token must be rejected"
    )


async def test_verifier_rejects_forged_token(
    verifier: AccessTokenVerifier, forged_token: str
) -> None:
    """A token signed with another secret is rejected."""
    assert await verifier.verify_token(forged_token) is None, (
        "a token with a wrong signature must be rejected"
    )


def test_current_user_falls_back_to_local_user(
    user_id: str,
) -> None:
    """Without a token, the configured local user is the caller."""
    assert current_user(user_id) == user_id, (
        "a stdio session must act as its local user"
    )


def test_current_user_requires_an_identity(
    unknown_caller_message: str,
) -> None:
    """Without a token or a local user, the call is refused."""
    with pytest.raises(ToolError, match=unknown_caller_message):
        current_user(None)


async def test_forwarded_identity_drops_unverified_user(
    forwarding_client: httpx2.AsyncClient,
    fake_support: FakeSupport,
    conversations_path: str,
    spoofed_user: str,
    identity_header: str,
) -> None:
    """Outside an authenticated request, a claimed user is removed."""
    response = await forwarding_client.post(
        conversations_path,
        headers={identity_header: spoofed_user},
    )
    assert (
        response.status_code == httpx2.codes.UNPROCESSABLE_CONTENT
    ), "the service must not receive an identity nobody verified"
    assert fake_support.calls == [], (
        "no conversation may be created for an unverified user"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
