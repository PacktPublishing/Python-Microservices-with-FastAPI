from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
import users
from authenticator import JWTAuthenticator, UserInfo
from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)


@dataclass
class GitHubTokens:
    access_token: str
    refresh_token: str



class GitHubAuthenticator(JWTAuthenticator):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        secret_key: str,
        session_factory: async_sessionmaker[AsyncSession],
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ) -> None:
        super().__init__(
            secret_key=secret_key,
            session_factory=session_factory,
            algorithm=algorithm,
            access_token_expire_minutes=access_token_expire_minutes,
            refresh_token_expire_days=refresh_token_expire_days,
        )
        self.client_id = client_id
        self.client_secret = client_secret

    def _make_http_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient()

    async def resolve_token(self, token: str) -> UserInfo | None:
        try:
            email = await self.get_user_email_from_github(token)
        except Exception:
            return None
        async with self.session_factory() as db:
            user_row = await users.get_user_by_email(
                db, email=email
            )
        if user_row is None:
            return None
        return UserInfo(email=user_row["email"], role=user_row["role"])  # ty: ignore[invalid-argument-type]

    async def get_user_email_from_github(
        self, access_token: str
    ) -> str:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with self._make_http_client() as client:
            response = await client.get(
                "https://api.github.com/user/emails",
                headers=headers,
            )
        response.raise_for_status()
        emails = response.json()
        return next(e["email"] for e in emails if e["primary"])

    def get_authorization_url(
        self, _redirect_uri: str, state: str
    ) -> str:
        params = {
            "client_id": self.client_id,
            # "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
        return (
            "https://github.com/login/oauth/authorize"
            f"?{urlencode(params)}"
        )

    async def _request_tokens(
        self, data: dict[str, str]
    ) -> GitHubTokens:
        async with self._make_http_client() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data=data,
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
        payload = response.json()
        return GitHubTokens(
            access_token=payload["access_token"],
            refresh_token=payload["refresh_token"],
        )


    async def exchange_code_for_token(
        self, code: str, redirect_uri: str
    ) -> GitHubTokens:
        return await self._request_tokens(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            }
        )


    async def refresh_access_token(
        self, refresh_token: str
    ) -> tuple[str, str]:
        async with self._make_http_client() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
        data = response.json()
        return data["access_token"], data["refresh_token"]

    async def resolve_refresh_token(
        self, token: str
    ) -> UserInfo | None:
        try:
            new_access_token, _ = await self.refresh_access_token(
                token
            )
            return await self.resolve_token(new_access_token)
        except Exception:
            return None


async def get_github_authenticator(
    request: Request,
) -> GitHubAuthenticator:
    return request.state.authenticator
