from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, TypedDict

from fastapi import Depends, FastAPI
from security.authenticators import (
    BaseAuthenticator,
    UnsafeAuthenticator,
)

from security.commons import UserInfo
from security.dependencies import GetUserWithRole, get_user
from security.router import router as security_router

# to get a string like this run:
# openssl rand -hex 32


class State(TypedDict):
    authenticator: BaseAuthenticator


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[State]:
    yield {"authenticator": UnsafeAuthenticator()}


app = FastAPI(lifespan=lifespan)
app.include_router(security_router)


@app.get("/users/me/")
async def read_users_me(
    current_user: Annotated[UserInfo, Depends(get_user)],
) -> UserInfo:
    return current_user


@app.get("/users/me/premium")
async def read_own_items(
    current_user: Annotated[
        UserInfo, Depends(GetUserWithRole("premium"))
    ],
):
    return current_user
