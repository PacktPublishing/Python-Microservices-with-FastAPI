from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from presentation.main import app


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    with TestClient(app=app) as client:
        yield client
