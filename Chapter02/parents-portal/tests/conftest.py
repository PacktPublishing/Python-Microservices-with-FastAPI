import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def test_client():
    """Create a TestClient for the app, shared across all tests in the module."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_cookies(test_client):
    """Clear cookies after each test to ensure test isolation."""
    yield
    test_client.cookies.clear()
