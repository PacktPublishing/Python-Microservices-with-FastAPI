import logging
from collections.abc import Iterator

import pytest
from dependencies import get_quote_repository
from fakes import FakeQuoteRepository
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def test_client() -> Iterator[TestClient]:
    app.dependency_overrides[get_quote_repository] = (
        FakeQuoteRepository
    )
    with TestClient(app=app) as client:
        yield client
    app.dependency_overrides.clear()


def test_get_quote_uses_fake_repository(
    test_client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    response = test_client.get("/quote")
    assert response.status_code == 200
    assert response.json() == {"quote": "This is a test quote."}
    assert "testing connection" in caplog.text
