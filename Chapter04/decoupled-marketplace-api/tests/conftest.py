import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Provides a test client with automatic cleanup."""
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
