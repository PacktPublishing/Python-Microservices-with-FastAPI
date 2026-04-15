from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from .authenticators import BaseAuthenticator
from .commons import UserInfo

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "me": "Read information about the current user.",
        "items": "Read items.",
    },
)


async def get_authenticator(
    request: Request,
) -> BaseAuthenticator:
    return request.state.authenticator


async def get_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    authenticator: Annotated[
        BaseAuthenticator, Depends(get_authenticator)
    ],
) -> UserInfo:
    user = await authenticator.resolve_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return user


class GetUserWithRole:
    def __init__(self, role: str):
        self.role = role

    async def __call__(
        self, user: Annotated[UserInfo, Depends(get_user)]
    ):
        if self.role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission",
            )
        return user
