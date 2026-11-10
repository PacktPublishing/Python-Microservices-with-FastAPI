from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import httpx2
import jwt
from fastmcp.exceptions import ToolError
from fastmcp.server.auth import AccessToken
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token
from loguru import logger

from .config import AuthSettings

ALGORITHM = "HS256"


def token_subject() -> str | None:
    """Read the user from the access token of the current request.

    Returns:
        str | None:
            The token subject, or `None` outside an authenticated request.
    """
    token = get_access_token()
    return None if token is None else token.subject


def current_user(local_user: str | None) -> str:
    """Identify the caller of a tool.

    Args:
        local_user (str | None):
            Identity configured for a local stdio session.

    Returns:
        str:
            The token subject over HTTP, otherwise the local user.

    Raises:
        ToolError:
            Neither a token nor a local user identifies the caller.
    """
    user = token_subject() or local_user
    if user is None:
        raise ToolError("Unknown caller: sign in first")
    return user


class AccessTokenVerifier(JWTVerifier):
    """Accept Chapter 8 access tokens and reject refresh tokens."""

    async def verify_token(
        self, token: str
    ) -> AccessToken | None:
        """Verify the signature and expiry, then the token type.

        Args:
            token (str):
                The bearer token sent by the MCP client.

        Returns:
            AccessToken | None:
                The verified token, or `None` to reject the request.
        """
        access = await super().verify_token(token)
        if access is None:
            return None
        if access.claims.get("type") != "access":
            logger.debug(
                "Rejected a token that is not an access token"
            )
            return None
        return access


def build_verifier(
    settings: AuthSettings,
) -> AccessTokenVerifier:
    """Verify tokens signed with the secret shared with Chapter 8.

    Args:
        settings (AuthSettings):
            Holds the shared secret.

    Returns:
        AccessTokenVerifier:
            A verifier for HS256 access tokens.
    """
    return AccessTokenVerifier(
        public_key=settings.jwt_secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )


def create_token(settings: AuthSettings, subject: str) -> str:
    """Sign an access token with the claims this server checks.

    Args:
        settings (AuthSettings):
            Shared secret and token lifetime.

        subject (str):
            The user the token identifies.

    Returns:
        str:
            The encoded JWT.
    """
    expires = datetime.now(UTC) + timedelta(
        minutes=settings.token_minutes
    )
    claims = {"sub": subject, "type": "access", "exp": expires}
    secret = settings.jwt_secret_key.get_secret_value()
    return jwt.encode(claims, secret, algorithm=ALGORITHM)


class ForwardedIdentity(httpx2.Auth):
    """Forward the token subject to the support service."""

    def auth_flow(
        self, request: httpx2.Request
    ) -> Generator[httpx2.Request, httpx2.Response]:
        """Set `X-User-Id` from the token, overriding any caller value.

        Args:
            request (httpx2.Request):
                The outgoing request to the support service.

        Yields:
            httpx2.Request:
                The request, with the caller's identity when known.
        """
        user = token_subject()
        if user is None:
            request.headers.pop("X-User-Id", None)
        else:
            request.headers["X-User-Id"] = user
        yield request
