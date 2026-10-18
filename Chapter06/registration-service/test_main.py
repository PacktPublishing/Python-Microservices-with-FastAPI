from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from database import get_db
from main import app
from models import Base

TEST_DB_PATH = "./test_users.db"


schema_engine = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
)


test_engine = create_async_engine(
    f"sqlite+aiosqlite:///{TEST_DB_PATH}",
)


session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def database() -> Generator[None]:
    Base.metadata.create_all(schema_engine)
    yield
    Base.metadata.drop_all(schema_engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def parent_payload() -> dict[str, str]:
    return {
        "email": "sofia.ricci@example.com",
        "full_name": "Sofia Ricci",
        "password": "aVeryStrongPassword",
        "role": "parent",
    }


def test_register_user(
    client: TestClient,
    parent_payload: dict[str, str],
) -> None:
    response = client.post("/users", json=parent_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "sofia.ricci@example.com"
    assert body["role"] == "parent"
    assert body["is_active"] is True
    assert "id" in body


def test_password_is_never_returned(
    client: TestClient,
    parent_payload: dict[str, str],
) -> None:
    response = client.post("/users", json=parent_payload)

    body = response.json()
    assert "password" not in body
    assert "hashed_password" not in body


def test_duplicate_email_is_rejected(
    client: TestClient,
    parent_payload: dict[str, str],
) -> None:
    client.post("/users", json=parent_payload)
    response = client.post("/users", json=parent_payload)

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A user with this email already exists"
    )


def test_short_password_is_rejected(
    client: TestClient,
    parent_payload: dict[str, str],
) -> None:
    parent_payload["password"] = "short"
    response = client.post("/users", json=parent_payload)

    assert response.status_code == 422


def test_read_user(
    client: TestClient,
    parent_payload: dict[str, str],
) -> None:
    created = client.post("/users", json=parent_payload)
    user_id = created.json()["id"]

    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    assert response.json()["full_name"] == "Sofia Ricci"


def test_read_missing_user(client: TestClient) -> None:
    response = client.get("/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_edit_missing_user(client: TestClient) -> None:
    response = client.patch(
        "/users/999",
        json={"full_name": "Sofia Ricci-Moretti"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_remove_missing_user(client: TestClient) -> None:
    response = client.delete("/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_edit_user(
    client: TestClient,
    parent_payload: dict[str, str],
) -> None:
    created = client.post("/users", json=parent_payload)
    user_id = created.json()["id"]

    response = client.patch(
        f"/users/{user_id}",
        json={"full_name": "Sofia Ricci-Moretti"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Sofia Ricci-Moretti"
    assert body["role"] == "parent"


def test_remove_user(
    client: TestClient,
    parent_payload: dict[str, str],
) -> None:
    created = client.post("/users", json=parent_payload)
    user_id = created.json()["id"]

    response = client.delete(f"/users/{user_id}")

    assert response.status_code == 204
    assert client.get(f"/users/{user_id}").status_code == 404
