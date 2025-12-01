"""Tests for user API endpoints."""


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_user(client):
    """Test creating a user via API."""
    response = client.post(
        "/users/",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"
    assert data["role"] == "parent"
    assert data["status"] == "active"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_create_user_with_role(client):
    """Test creating a user with specific role."""
    response = client.post(
        "/users/",
        json={
            "name": "Sitter User",
            "email": "sitter@example.com",
            "password": "password123",
            "role": "sitter",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "sitter"


def test_create_user_invalid_email(client):
    """Test creating user with invalid email fails."""
    response = client.post(
        "/users/",
        json={
            "name": "Test User",
            "email": "not-an-email",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_create_user_short_password(client):
    """Test creating user with short password fails."""
    response = client.post(
        "/users/",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_get_user(client):
    """Test getting a user by ID."""
    create_response = client.post(
        "/users/",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    user_id = create_response.json()["id"]

    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == "Test User"


def test_get_user_not_found(client):
    """Test getting non-existent user returns 404."""
    response = client.get("/users/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_list_users(client):
    """Test listing users."""
    for i in range(3):
        client.post(
            "/users/",
            json={
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "password": "password123",
            },
        )

    response = client.get("/users/")

    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total_count" in data
    assert data["total_count"] == 3
    assert len(data["users"]) == 3


def test_list_users_pagination(client):
    """Test listing users with pagination."""
    for i in range(5):
        client.post(
            "/users/",
            json={
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "password": "password123",
            },
        )

    response = client.get("/users/?page=1&page_size=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 2
    assert data["total_count"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_list_users_filter_by_role(client):
    """Test listing users filtered by role."""
    client.post(
        "/users/",
        json={
            "name": "Parent User",
            "email": "parent@example.com",
            "password": "password123",
            "role": "parent",
        },
    )
    client.post(
        "/users/",
        json={
            "name": "Sitter User",
            "email": "sitter@example.com",
            "password": "password123",
            "role": "sitter",
        },
    )

    response = client.get("/users/?role=sitter")

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["users"][0]["role"] == "sitter"


def test_update_user(client):
    """Test updating a user."""
    create_response = client.post(
        "/users/",
        json={
            "name": "Original Name",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    user_id = create_response.json()["id"]

    response = client.patch(
        f"/users/{user_id}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["email"] == "test@example.com"


def test_update_user_not_found(client):
    """Test updating non-existent user returns 404."""
    response = client.patch(
        "/users/99999",
        json={"name": "New Name"},
    )

    assert response.status_code == 404


def test_delete_user(client):
    """Test deleting a user."""
    create_response = client.post(
        "/users/",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        },
    )
    user_id = create_response.json()["id"]

    response = client.delete(f"/users/{user_id}")

    assert response.status_code == 204

    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 404


def test_delete_user_not_found(client):
    """Test deleting non-existent user returns 404."""
    response = client.delete("/users/99999")

    assert response.status_code == 404
