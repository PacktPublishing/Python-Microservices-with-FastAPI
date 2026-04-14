from ..commons import UserInfo
from .base import BaseAuthenticator


class UnsafeAuthenticator(BaseAuthenticator):
    async def verify_user_and_password(
        self, username: str, password: str
    ) -> UserInfo:
        _ = password
        return UserInfo(
            username=username, roles={"standard", "premium"}
        )

    async def generate_user_token(
        self, username, password
    ) -> str:
        user = await self.verify_user_and_password(
            username, password
        )
        return f"tokenized{user.username}"

    async def resolve_token(self, token) -> UserInfo | None:
        if token.startswith("tokenized"):
            return UserInfo(
                username=token.removeprefix("tokenized")
            )
