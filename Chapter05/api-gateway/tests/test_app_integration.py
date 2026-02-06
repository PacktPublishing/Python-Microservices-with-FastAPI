from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleware import RateLimiter, RateLimitMiddleware
from routers import aggregation_router
from services import MockPortalClient, MockReservationClient


@pytest.fixture
def mock_portal_client():
    return MockPortalClient()


@pytest.fixture
def mock_reservation_client():
    return MockReservationClient()


@pytest.fixture
def populated_reservation_client(mock_reservation_client):
    """Reservation client with pre-populated slots."""
    slots_data = [
        {
            "week_day": "monday",
            "time_slot": "morning",
            "babysitter_name": "Alice",
            "status": "available",
        },
        {
            "week_day": "monday",
            "time_slot": "afternoon",
            "babysitter_name": "Bob",
            "status": "available",
        },
        {
            "week_day": "tuesday",
            "time_slot": "morning",
            "babysitter_name": "Charlie",
            "status": "pending",
        },
        {
            "week_day": "wednesday",
            "time_slot": "night",
            "babysitter_name": "Diana",
            "status": "available",
        },
    ]
    for slot_data in slots_data:
        slot_id = uuid4()
        mock_reservation_client.slots[slot_id] = {
            "id": str(slot_id),
            **slot_data,
        }
    return mock_reservation_client


@pytest.fixture
def rate_limiter():
    rate_limiter = RateLimiter()
    rate_limiter.add_rule(
        path_matcher=lambda p: p.startswith("/aggregate"),
        requests_per_minute=5,
        burst_size=5,
    )
    return rate_limiter


@pytest.fixture
def app_with_rate_limiter(
    mock_portal_client, populated_reservation_client, rate_limiter
):
    """Create app with mock clients and rate limiter using lifespan."""

    @asynccontextmanager
    async def test_lifespan(app: FastAPI) -> AsyncIterator[dict]:
        yield {
            "portal_client": mock_portal_client,
            "reservation_client": populated_reservation_client,
        }

    app = FastAPI(lifespan=test_lifespan)

    # Configure rate limiter
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=rate_limiter,
    )
    app.include_router(aggregation_router)

    return app, mock_portal_client, populated_reservation_client


@pytest.fixture
def client(app_with_rate_limiter):
    app, _, _ = app_with_rate_limiter
    with TestClient(app) as test_client:
        yield test_client


class TestAppWithRateLimiter:
    """Integration tests for app with rate limiter and mock clients."""

    def test_dashboard_includes_rate_limit_headers(self, client):
        """Test dashboard response includes rate limit headers."""
        response = client.get("/aggregate/dashboard")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_rate_limit_decrements(self, client):
        """Test rate limit remaining decrements with requests."""
        response1 = client.get("/aggregate/dashboard")
        remaining1 = int(
            response1.headers["X-RateLimit-Remaining"]
        )

        response2 = client.get("/aggregate/dashboard")
        remaining2 = int(
            response2.headers["X-RateLimit-Remaining"]
        )

        assert remaining2 < remaining1

    def test_rate_limit_exceeded_returns_429(self, client):
        """Test exceeding rate limit returns 429."""
        # Exhaust the rate limit (burst_size=5)
        for _ in range(5):
            client.get("/aggregate/dashboard")

        # Next request should be blocked
        response = client.get("/aggregate/dashboard")

        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
        assert "Retry-After" in response.headers

    def test_same_endpoint_rate_limited(self, client):
        """Test same endpoint is rate limited after burst."""
        # Make requests to same endpoint until limit
        for _ in range(5):
            response = client.get("/aggregate/dashboard")
            assert response.status_code == 200

        # Next request to same endpoint should be blocked
        response = client.get("/aggregate/dashboard")

        assert response.status_code == 429

    def test_successful_response_with_mock_data(self, client):
        """Test successful response contains mock data."""
        response = client.get("/aggregate/dashboard")

        assert response.status_code == 200
        data = response.json()

        assert (
            "Welcome to Babysitting Service"
            in data["welcome_content"]
        )
        assert data["total_available"] == 3
        assert len(data["available_slots"]) == 3

    def test_health_endpoint_with_healthy_services(self, client):
        """Test health endpoint when services are healthy."""
        response = client.get("/aggregate/health")

        assert response.status_code == 200
        data = response.json()

        assert data["gateway"] == "healthy"
        assert data["portal_service"] is True
        assert data["reservation_service"] is True
        assert data["all_healthy"] is True

    def test_health_endpoint_with_unhealthy_portal(
        self, app_with_rate_limiter
    ):
        """Test health when portal is unhealthy."""
        app, portal_client, _ = app_with_rate_limiter
        portal_client.is_healthy = False

        with TestClient(app) as client:
            response = client.get("/aggregate/health")

            assert response.status_code == 200
            data = response.json()

            assert data["portal_service"] is False
            assert data["all_healthy"] is False

    def test_availability_summary_with_filter(self, client):
        """Test availability summary with filter."""
        response = client.get(
            "/aggregate/availability-summary?week_day=monday"
        )

        assert response.status_code == 200
        data = response.json()

        # Only Monday available slots
        assert data["total_slots"] == 2
        for slot in data["slots"]:
            assert slot["week_day"] == "monday"


class TestRateLimiterMiddlewareIntegration:
    """Tests for rate limiter middleware behavior."""

    def test_x_forwarded_for_client_isolation(
        self, app_with_rate_limiter
    ):
        """Test different clients via X-Forwarded-For are isolated."""
        app, _, _ = app_with_rate_limiter

        with TestClient(app) as client:
            # Exhaust rate limit for client 1.2.3.4
            for _ in range(5):
                client.get(
                    "/aggregate/dashboard",
                    headers={"X-Forwarded-For": "1.2.3.4"},
                )

            # Client 1.2.3.4 should be blocked
            response1 = client.get(
                "/aggregate/dashboard",
                headers={"X-Forwarded-For": "1.2.3.4"},
            )
            assert response1.status_code == 429

            # Client 5.6.7.8 should still have quota
            response2 = client.get(
                "/aggregate/dashboard",
                headers={"X-Forwarded-For": "5.6.7.8"},
            )
            assert response2.status_code == 200

    def test_rate_limit_429_includes_retry_after(
        self, app_with_rate_limiter
    ):
        """Test 429 response includes Retry-After header."""
        app, _, _ = app_with_rate_limiter

        with TestClient(app) as client:
            # Exhaust rate limit
            for _ in range(5):
                client.get("/aggregate/dashboard")

            response = client.get("/aggregate/dashboard")

            assert response.status_code == 429
            assert "Retry-After" in response.headers
            retry_after = int(response.headers["Retry-After"])
            assert retry_after >= 1

    def test_rate_limit_response_body(
        self, app_with_rate_limiter
    ):
        """Test 429 response body format."""
        app, _, _ = app_with_rate_limiter

        with TestClient(app) as client:
            # Exhaust rate limit
            for _ in range(5):
                client.get("/aggregate/dashboard")

            response = client.get("/aggregate/dashboard")

            assert response.status_code == 429
            data = response.json()
            assert "detail" in data
            assert "retry_after" in data
