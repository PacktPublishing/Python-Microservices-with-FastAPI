from abc import ABC, abstractmethod

from ..commons import UserInfo


class BaseAuthenticator(ABC):
    @abstractmethod
    async def verify_user_and_password(
        self, username: str, password: str
    ) -> UserInfo | None:
        pass

    @abstractmethod
    async def generate_user_token(
        self, username: str, password: str
    ) -> str:
        pass

    @abstractmethod
    async def resolve_token(
        self, token: str
    ) -> UserInfo | None:
        pass
