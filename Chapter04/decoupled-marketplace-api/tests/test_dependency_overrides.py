"""
Tests demonstrating FastAPI's dependency override system.

This module shows how to use dependency_overrides to replace
real dependencies with mocks during testing, enabling isolated
unit tests without external services.
"""

from app.dependencies import (
    User,
    get_auth_service,
    get_pagination_helper,
)
from app.main import app


class MockPaginationHelper:
    """Mock pagination helper for testing."""

    def __init__(self):
        self.paginate_calls = []

    def paginate_items(
        self, items: list, page: int, page_size: int
    ) -> dict:
        self.paginate_calls.append(
            {
                "items_count": len(items),
                "page": page,
                "page_size": page_size,
            }
        )
        return {
            "data": [{"id": 1, "name": "Mock Sitter"}],
            "current_page": page,
            "page_size": 1,
            "total_pages": 1,
            "total_items": 1,
        }


class MockAuthService:
    """Mock authentication service for testing."""

    def __init__(self):
        self.login_attempts = []

    async def authenticate_user(
        self, username: str, password: str
    ) -> dict | None:
        self.login_attempts.append(username)
        if username == "testuser" and password == "password123":
            return {"username": "testuser", "id": 1}
        return None

    async def get_user_from_token(
        self, token: str
    ) -> User | None:
        if token == "valid_test_token":
            return User(
                id=1,
                username="testuser",
                email="test@example.com",
            )
        return None

    def create_access_token(self, user: dict) -> str:
        return f"mock_token_for_{user['username']}"


class TestDependencyOverrides:
    """Tests demonstrating dependency override patterns."""

    def test_override_pagination_helper(self, client):
        """
        Test overriding PaginationHelper with a mock.

        This demonstrates how to replace a dependency with a mock
        to control behavior during testing.
        """
        mock_helper = MockPaginationHelper()
        app.dependency_overrides[get_pagination_helper] = (
            lambda: mock_helper
        )

        response = client.get("/sitters/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == [{"id": 1, "name": "Mock Sitter"}]
        assert len(mock_helper.paginate_calls) == 1

        app.dependency_overrides.clear()

    def test_override_auth_service(self, client):
        """
        Test overriding AuthService with a mock.

        This shows how authentication can be mocked for testing
        protected endpoints without real tokens.
        """
        mock_auth = MockAuthService()
        app.dependency_overrides[get_auth_service] = (
            lambda: mock_auth
        )

        app.dependency_overrides.clear()

    def test_multiple_overrides(self, client):
        """
        Test with multiple dependency overrides.

        Demonstrates that multiple dependencies can be overridden
        simultaneously for complex integration tests.
        """
        mock_pagination = MockPaginationHelper()
        mock_auth = MockAuthService()

        app.dependency_overrides[get_pagination_helper] = (
            lambda: mock_pagination
        )
        app.dependency_overrides[get_auth_service] = (
            lambda: mock_auth
        )

        response = client.get("/sitters/")
        assert response.status_code == 200
        assert len(mock_pagination.paginate_calls) == 1

        app.dependency_overrides.clear()

    def test_override_cleanup(self, client):
        """
        Test that overrides are properly cleaned up.

        Verifies that clearing dependency_overrides restores
        original behavior.
        """
        mock_helper = MockPaginationHelper()
        app.dependency_overrides[get_pagination_helper] = (
            lambda: mock_helper
        )

        response1 = client.get("/sitters/")
        assert response1.json()["total_items"] == 1

        app.dependency_overrides.clear()

        response2 = client.get("/sitters/")
        assert response2.json()["total_items"] == 10000


class TestMockBehaviorVerification:
    """Tests that verify mock behavior was called correctly."""

    def test_pagination_receives_correct_parameters(self, client):
        """Verify pagination helper receives correct params."""
        mock_helper = MockPaginationHelper()
        app.dependency_overrides[get_pagination_helper] = (
            lambda: mock_helper
        )

        client.get("/sitters/?page=3&page_size=50")

        assert len(mock_helper.paginate_calls) == 1
        call = mock_helper.paginate_calls[0]
        assert call["page"] == 3
        assert call["page_size"] == 50

        app.dependency_overrides.clear()

    def test_multiple_endpoint_calls_tracked(self, client):
        """Verify mock tracks multiple calls."""
        mock_helper = MockPaginationHelper()
        app.dependency_overrides[get_pagination_helper] = (
            lambda: mock_helper
        )

        client.get("/sitters/?page=1")
        client.get("/sitters/?page=2")
        client.get("/parents/?page=1")

        assert len(mock_helper.paginate_calls) == 3

        app.dependency_overrides.clear()
