"""Tests for API endpoints with dependency injection."""


def test_root_endpoint(client):
    """Test root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


class TestSittersEndpoint:
    """Tests for /sitters endpoints."""

    def test_get_sitters_default_pagination(self, client):
        """Test getting sitters with default pagination."""
        response = client.get("/sitters/")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "current_page" in data
        assert "total_items" in data
        assert data["current_page"] == 1
        assert len(data["data"]) == 20

    def test_get_sitters_custom_page(self, client):
        """Test getting sitters with custom page number."""
        response = client.get("/sitters/?page=2&page_size=10")
        assert response.status_code == 200

        data = response.json()
        assert data["current_page"] == 2
        assert len(data["data"]) == 10
        assert data["data"][0]["id"] == 11

    def test_get_sitters_large_page_size(self, client):
        """Test getting sitters with large page size."""
        response = client.get("/sitters/?page=1&page_size=100")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 100

    def test_get_sitters_page_size_exceeds_max(self, client):
        """Test that page_size is capped at maximum."""
        response = client.get("/sitters/?page_size=200")
        assert response.status_code == 422

    def test_get_sitters_invalid_page(self, client):
        """Test that invalid page number returns error."""
        response = client.get("/sitters/?page=0")
        assert response.status_code == 422

    def test_get_sitters_configurable_endpoint(self, client):
        """Test the configurable pagination endpoint."""
        response = client.get("/sitters/configurable?page=1")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data

    def test_get_single_sitter(self, client):
        """Test getting a single sitter by ID."""
        response = client.get("/sitters/1")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == 1
        assert "name" in data
        assert "hourly_rate" in data

    def test_get_sitter_not_found(self, client):
        """Test getting a non-existent sitter."""
        response = client.get("/sitters/99999")
        assert response.status_code == 200
        assert response.json() == {"error": "Sitter not found"}


class TestParentsEndpoint:
    """Tests for /parents endpoints."""

    def test_get_parents_default_pagination(self, client):
        """Test getting parents with default pagination."""
        response = client.get("/parents/")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["current_page"] == 1
        assert len(data["data"]) == 15

    def test_get_parents_custom_pagination(self, client):
        """Test getting parents with custom pagination."""
        response = client.get("/parents/?page=3&page_size=25")
        assert response.status_code == 200

        data = response.json()
        assert data["current_page"] == 3
        assert len(data["data"]) == 25

    def test_get_single_parent(self, client):
        """Test getting a single parent by ID."""
        response = client.get("/parents/1")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == 1
        assert "name" in data
        assert "children_count" in data
