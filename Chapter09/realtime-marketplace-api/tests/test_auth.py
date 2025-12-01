import uuid

import pytest
from httpx import AsyncClient


def unique_email():
    """Generate a unique email for test isolation."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


async def test_register_user(client: AsyncClient):
    """Test user registration."""
    email = unique_email()
    response = await client.post(
        "/auth/register",
        json={
            "name": "New User",
            "email": email,
            "password": "password123",
            "role": "parent",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New User"
    assert data["email"] == email
    assert "password" not in data


async def test_register_duplicate_email(client: AsyncClient):
    """Test that duplicate emails are rejected."""
    email = unique_email()
    await client.post(
        "/auth/register",
        json={
            "name": "First User",
            "email": email,
            "password": "password123",
        },
    )

    response = await client.post(
        "/auth/register",
        json={
            "name": "Second User",
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 409


async def test_login_success(client: AsyncClient):
    """Test successful login."""
    email = unique_email()
    await client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": email,
            "password": "password123",
        },
    )

    response = await client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "password123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    """Test login with wrong password."""
    email = unique_email()
    await client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": email,
            "password": "password123",
        },
    )

    response = await client.post(
        "/auth/login",
        data={
            "username": email,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


async def test_get_current_user(
    client: AsyncClient, test_parent, parent_token
):
    """Test getting current user with valid token."""
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {parent_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_parent.email


async def test_get_current_user_invalid_token(client: AsyncClient):
    """Test that invalid token is rejected."""
    response = await client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )

    assert response.status_code == 401
