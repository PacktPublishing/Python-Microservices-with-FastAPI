import httpx
import pytest
import respx
from authenticator import JWTAuthenticator, get_authenticator
from fake_authenticator import FakeAuthenticator
from fastapi.testclient import TestClient
from github_auth import GitHubAuthenticator
from main import app
from security import hash_password
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from users import metadata, users

TEST_DB_PATH = "./test_auth_users.db"

schema_engine = create_engine(f"sqlite:///{TEST_DB_PATH}")
test_engine = create_async_engine(f"sqlite+aiosqlite:///{TEST_DB_PATH}")
session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
def database():
    metadata.create_all(schema_engine)
    yield
    metadata.drop_all(schema_engine)


# ---------------------------------------------------------------------------
# FakeAuthenticator tests
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_authenticator] = FakeAuthenticator
    return TestClient(app)


def test_babysitter_route_rejects_a_parent(client: TestClient) -> None:
    login = client.post(
        "/token",
        data={
            "username": "sofia.ricci@example.com",
            "password": "aVeryStrongPassword",
        },
    )
    token = login.json()["access_token"]

    response = client.get(
        "/babysitters/me/schedule",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# JWTAuthenticator tests
# ---------------------------------------------------------------------------


@pytest.fixture
def jwt_client() -> TestClient:
    app.dependency_overrides[get_authenticator] = lambda: JWTAuthenticator(
        secret_key="test-secret",
        session_factory=session_factory,
    )
    return TestClient(app)


@pytest.fixture
def babysitter() -> dict[str, str]:
    payload = {
        "email": "amara.osei@example.com",
        "password": "aVeryStrongPassword",
    }
    with schema_engine.begin() as conn:
        conn.execute(
            users.insert(),
            {
                "email": payload["email"],
                "hashed_password": hash_password(payload["password"]),
                "role": "babysitter",
            },
        )
    return payload


def test_login_and_refresh(
    jwt_client: TestClient, babysitter: dict[str, str]
) -> None:
    login = jwt_client.post(
        "/token",
        data={
            "username": babysitter["email"],
            "password": babysitter["password"],
        },
    )
    assert login.status_code == 200
    tokens = login.json()

    refreshed = jwt_client.post(
        "/token/refresh",
        params={"refresh_token": tokens["refresh_token"]},
    )

    assert refreshed.status_code == 200
    assert "access_token" in refreshed.json()


# ---------------------------------------------------------------------------
# GitHubAuthenticator tests
# ---------------------------------------------------------------------------


@pytest.fixture
def github_authenticator(monkeypatch: pytest.MonkeyPatch) -> GitHubAuthenticator:
    auth = GitHubAuthenticator(
        client_id="test-client-id",
        client_secret="test-client-secret",
        secret_key="test-secret",
        session_factory=session_factory,
    )
    # verify=False avoids loading system CA certs, which crashes on some
    # Windows configurations; respx still intercepts the request.
    monkeypatch.setattr(auth, "_make_http_client", lambda: httpx.AsyncClient(verify=False))
    return auth


async def test_github_resolve_token_success(
    respx_mock: respx.MockRouter,
    github_authenticator: GitHubAuthenticator,
    babysitter: dict[str, str],
) -> None:
    respx_mock.get("https://api.github.com/user/emails").mock(
        return_value=httpx.Response(
            200,
            json=[{"email": babysitter["email"], "primary": True}],
        )
    )
    result = await github_authenticator.resolve_token("fake-gh-token")
    assert result is not None
    assert result.email == babysitter["email"]


async def test_github_resolve_token_unknown_email(
    respx_mock: respx.MockRouter,
    github_authenticator: GitHubAuthenticator,
) -> None:
    respx_mock.get("https://api.github.com/user/emails").mock(
        return_value=httpx.Response(
            200,
            json=[{"email": "ghost@example.com", "primary": True}],
        )
    )
    result = await github_authenticator.resolve_token("fake-gh-token")
    assert result is None
