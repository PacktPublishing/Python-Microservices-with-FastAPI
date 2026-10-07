import os
import secrets
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any, TypedDict

import users
from authenticator import (
    BaseAuthenticator,
    GetUserWithRole,
    UserInfo,
    get_authenticator,
    get_current_user,
)
from database import async_session, engine, get_db
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from github_auth import (
    GitHubAuthenticator,
    get_github_authenticator,
)
from schemas import RefreshTokenRequest, Token, UserRead
from settings import settings
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware


class State(TypedDict):
    authenticator: BaseAuthenticator


JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY",
    "4f8e2b6a1c9d3f7e5a0b8c2d6e4f1a9b3c7d5e8f2a6b0c4d8e1f3a7b5c9d2e6f",
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[State]:
    yield {
        # "authenticator": FakeAuthenticator()
        # "authenticator": JWTAuthenticator(
        #     secret_key=settings.jwt_secret_key,
        #     session_factory=async_session,
        # )
        "authenticator": GitHubAuthenticator(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            secret_key=settings.jwt_secret_key,
            session_factory=async_session,
        ),
    }
    await engine.dispose()


app = FastAPI(title="Authenticator Service", lifespan=lifespan)

DbSession = Annotated[AsyncSession, Depends(get_db)]

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
)


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    authenticator: Annotated[
        BaseAuthenticator, Depends(get_authenticator)
    ],
) -> Token:
    user = await authenticator.verify_user_and_password(
        form_data.username, form_data.password
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return Token(
        access_token=await authenticator.create_access_token(user),
        refresh_token=await authenticator.create_refresh_token(user),
    )

@app.post("/token/refresh")
async def refresh_access_token(
    refresh_token: str,
    authenticator: Annotated[
        BaseAuthenticator, Depends(get_authenticator)
    ],
) -> Token:
    user = await authenticator.resolve_refresh_token(
        refresh_token
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    return Token(
        access_token=await authenticator.create_access_token(
            user
        ),
        refresh_token=await authenticator.create_refresh_token(
            user
        ),
    )


@app.get("/users/me", response_model=UserRead)
async def read_current_user(
    user: Annotated[UserInfo, Depends(get_current_user)],
) -> Any:
    return user


@app.get("/babysitters/me/schedule", response_model=UserRead)
async def read_my_schedule(
    user: Annotated[
        UserInfo, Depends(GetUserWithRole("babysitter"))
    ],
) -> Any:
    return user


@app.post("/auth/github/refresh")
async def github_refresh(
    body: RefreshTokenRequest,
    github_authenticator: Annotated[
        GitHubAuthenticator,
        Depends(get_github_authenticator),
    ],
) -> Token:
    try:
        (
            access_token,
            refresh_token,
        ) = await github_authenticator.refresh_access_token(
            body.refresh_token
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@app.get("/auth/github/login")
async def github_login(
    request: Request,
    github_authenticator: Annotated[
        GitHubAuthenticator,
        Depends(get_github_authenticator),
    ],
) -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    redirect_uri = str(request.url_for("github_callback"))
    url = github_authenticator.get_authorization_url(
        redirect_uri,
        state=state,
    )
    return RedirectResponse(url)


@app.get("/auth/github/callback")
async def github_callback(
    code: str,
    state: str,
    request: Request,
    db: DbSession,
    github_authenticator: Annotated[
        GitHubAuthenticator,
        Depends(get_github_authenticator),
    ],
) -> Token:
    if state != request.session.get("oauth_state"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    redirect_uri = str(request.url_for("github_callback"))
    tokens = await github_authenticator.exchange_code_for_token(
        code, redirect_uri
    )
    email = await github_authenticator.get_user_email_from_github(
        tokens.access_token
    )

    user_row = await users.get_user_by_email(db, email=email)
    if user_row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found for this email",
        )
    return Token(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )
