from authenticator import BaseAuthenticator, Role, UserInfo


class FakeAuthenticator(BaseAuthenticator):
    def __init__(self) -> None:
        self._users: dict[str, tuple[str, Role]] = {
            "sofia.ricci@example.com": (
                self._fake_hash("aVeryStrongPassword"),
                "parent",
            ),
            "marco.bianchi@example.com": (
                self._fake_hash("anotherStrongPassword"),
                "babysitter",
            ),
        }

    @staticmethod
    def _fake_hash(password: str) -> str:
        return f"{password}hashed"

    async def verify_user_and_password(
        self, email: str, password: str
    ) -> UserInfo | None:
        stored = self._users.get(email)
        if stored is None:
            return None
        hashed, role = stored
        if hashed != self._fake_hash(password):
            return None
        return UserInfo(email=email, role=role)

    async def create_access_token(self, user: UserInfo) -> str:
        scopes = ",".join(user.scopes)
        return f"fake::{user.email}::{user.role}::{scopes}"

    async def resolve_token(self, token: str) -> UserInfo | None:
        try:
            _, email, role, *_ = token.split("::")
        except ValueError:
            return None
        return UserInfo(email=email, role=role)  # ty: ignore[invalid-argument-type]

    async def create_refresh_token(self, user):
        return await self.create_access_token(user)

    async def resolve_refresh_token(self, token):
        return await self.resolve_token(token)
