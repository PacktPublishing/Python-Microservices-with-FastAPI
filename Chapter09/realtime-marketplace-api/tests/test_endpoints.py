import pytest
from httpx import AsyncClient


async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["version"] == "1.0.0"


async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


async def test_protected_endpoint_requires_auth(
    client: AsyncClient,
):
    """Test that protected endpoints require authentication."""
    response = await client.get("/bookings/")

    assert response.status_code == 401


async def test_notifications_requires_auth(client: AsyncClient):
    """Test that notifications endpoint requires auth."""
    response = await client.get("/notifications/unread")

    assert response.status_code == 401


async def test_get_notifications_authenticated(
    client: AsyncClient, test_parent, parent_token
):
    """Test getting notifications when authenticated."""
    response = await client.get(
        "/notifications/unread",
        headers={"Authorization": f"Bearer {parent_token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_list_bookings_authenticated(
    client: AsyncClient, test_parent, parent_token
):
    """Test listing bookings when authenticated."""
    response = await client.get(
        "/bookings/",
        headers={"Authorization": f"Bearer {parent_token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
