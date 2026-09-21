from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

import jwt
import users
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from security import verify_password
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

Role = Literal["parent", "babysitter"]


@dataclass
class UserInfo:
    email: str
    role: Role
    scopes: list[str] = field(default_factory=list)


class BaseAuthenticator(ABC):
    @abstractmethod
    async def verify_user_and_password(
        self, email: str, password: str
    ) -> UserInfo | None:
        pass

    @abstractmethod
    async def create_access_token(self, user: UserInfo) -> str:
        pass

    @abstractmethod
    async def resolve_token(self, token: str) -> UserInfo | None:
        pass

    @abstractmethod
    async def create_refresh_token(self, user: UserInfo) -> str:
        pass

    @abstractmethod
    async def resolve_refresh_token(
        self, token: str
    ) -> UserInfo | None:
        pass


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_authenticator(
    request: Request,
) -> BaseAuthenticator:
    return request.state.authenticator


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    authenticator: Annotated[
        BaseAuthenticator, Depends(get_authenticator)
    ],
) -> UserInfo:
    user = await authenticator.resolve_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user


class GetUserWithRole:
    def __init__(self, role: Role) -> None:
        self.role = role

    async def __call__(
        self,
        user: Annotated[UserInfo, Depends(get_current_user)],
    ) -> UserInfo:
        if user.role != self.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user


class JWTAuthenticator(BaseAuthenticator):
    def __init__(
        self,
        secret_key: str,
        session_factory: async_sessionmaker[AsyncSession],
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ) -> None:
        self.secret_key = secret_key
        self.session_factory = session_factory
        self.algorithm = algorithm
        self.access_minutes = access_token_expire_minutes
        self.refresh_days = refresh_token_expire_days

    async def verify_user_and_password(
        self, email: str, password: str
    ) -> UserInfo | None:
        async with self.session_factory() as db:
            user = await users.get_user_by_email(db, email=email)
        if user is None:
            return None
        if not verify_password(password, user["hashed_password"]):
            return None
        return UserInfo(email=user["email"], role=user["role"])  # ty: ignore[invalid-argument-type]

    def _create_token(
        self,
        user: UserInfo,
        expires_delta: timedelta,
        token_type: str,
    ) -> str:
        expire = datetime.now(UTC) + expires_delta
        payload = {
            "sub": user.email,
            "role": user.role,
            "type": token_type,
            "exp": expire,
        }
        return jwt.encode(
            payload, self.secret_key, algorithm=self.algorithm
        )

    async def create_access_token(self, user: UserInfo) -> str:
        return self._create_token(
            user,
            timedelta(minutes=self.access_minutes),
            "access",
        )

    async def resolve_token(self, token: str) -> UserInfo | None:
        payload = self._decode(token)
        if payload is None or payload["type"] != "access":
            return None
        return UserInfo(email=payload["sub"], role=payload["role"])

    def _decode(self, token: str) -> dict | None:
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
        except jwt.PyJWTError:
            return None

    async def create_refresh_token(self, user: UserInfo) -> str:
        return self._create_token(
            user,
            timedelta(days=self.refresh_days),
            "refresh",
        )

    async def resolve_refresh_token(
        self, token: str
    ) -> UserInfo | None:
        payload = self._decode(token)
        if payload is None or payload["type"] != "refresh":
            return None
        return UserInfo(email=payload["sub"], role=payload["role"])
