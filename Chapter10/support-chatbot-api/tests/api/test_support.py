"""Tests for support API endpoints."""
from fastapi.testclient import TestClient

from main import app
from domain.support.views import get_support_service


def test_chat_endpoint_returns_200(mock_support_service):
    """Test that the chat endpoint responds with valid structure."""
    app.dependency_overrides[get_support_service] = lambda: mock_support_service

    client = TestClient(app)
    response = client.post(
        "/support/chat",
        json={"question": "Test question"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "could_answer" in data
    assert "confidence" in data
    assert data["could_answer"] is True

    app.dependency_overrides.clear()


def test_chat_endpoint_validates_input(mock_support_service):
    """Test that empty questions are rejected."""
    app.dependency_overrides[get_support_service] = lambda: mock_support_service

    client = TestClient(app)
    response = client.post(
        "/support/chat",
        json={"question": ""}
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_root_endpoint():
    """Test root endpoint returns API info."""
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint():
    """Test health check endpoint."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
