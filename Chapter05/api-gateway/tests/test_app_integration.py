from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIASGIMiddleware


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
def app_with_rate_limiter(
    mock_portal_client, populated_reservation_client, limiter
):
    """Create app with mock clients and rate limiter."""

    @asynccontextmanager
    async def test_lifespan(_app: FastAPI) -> AsyncGenerator[dict]:
        yield {
            "portal_client": mock_portal_client,
            "reservation_client": populated_reservation_client,
        }

    app = FastAPI(lifespan=test_lifespan)
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(
        _request: Request, exc: RateLimitExceeded
    ):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "retry_after": "60",
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(exc.detail),
            },
        )

    app.add_middleware(
        SlowAPIASGIMiddleware  # ty: ignore[invalid-argument-type]
    )

    # Add rate-limited endpoints for testing
    @app.get("/aggregate/availability-summary")
    @limiter.limit("5/minute")
    async def availability_summary(
        request: Request,
        response: Response,
        week_day: str | None = None,
        time_slot: str | None = None,
    ):
        del request, response
        from routers.aggregation import fetch_availability_summary

        return await fetch_availability_summary(
            populated_reservation_client,
            week_day=week_day,  # ty: ignore[invalid-argument-type]
            time_slot=time_slot,  # ty: ignore[invalid-argument-type]
        )

    @app.get("/aggregate/health")
    @limiter.limit("5/minute")
    async def health(request: Request, _response: Response):
        del request
        from routers.aggregation import fetch_aggregated_health

        return await fetch_aggregated_health(
            mock_portal_client, populated_reservation_client
        )

    return app, mock_portal_client, populated_reservation_client


@pytest.fixture
def client(app_with_rate_limiter):
    app, _, _ = app_with_rate_limiter
    with TestClient(app) as test_client:
        yield test_client


class TestAppWithRateLimiter:
    """Integration tests for app with rate limiter and mock clients."""

    def test_aggregate_includes_rate_limit_headers(self, client):
        """Test aggregate response includes rate limit headers."""
        response = client.get("/aggregate/availability-summary")

        assert response.status_code == 200
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers
        assert "x-ratelimit-reset" in response.headers

    def test_rate_limit_decrements(self, client):
        """Test rate limit remaining decrements with requests."""
        response1 = client.get("/aggregate/availability-summary")
        remaining1 = int(
            response1.headers["x-ratelimit-remaining"]
        )

        response2 = client.get("/aggregate/availability-summary")
        remaining2 = int(
            response2.headers["x-ratelimit-remaining"]
        )

        assert remaining2 < remaining1

    def test_rate_limit_exceeded_returns_429(self, client):
        """Test exceeding rate limit returns 429."""
        # Exhaust the rate limit (5/minute)
        for _ in range(5):
            client.get("/aggregate/availability-summary")

        # Next request should be blocked
        response = client.get("/aggregate/availability-summary")

        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
        assert "Retry-After" in response.headers

    def test_same_endpoint_rate_limited(self, client):
        """Test same endpoint is rate limited after burst."""
        # Make requests to same endpoint until limit
        for _ in range(5):
            response = client.get(
                "/aggregate/availability-summary"
            )
            assert response.status_code == 200

        # Next request to same endpoint should be blocked
        response = client.get("/aggregate/availability-summary")

        assert response.status_code == 429

    def test_successful_response_with_mock_data(self, client):
        """Test successful response contains mock data."""
        response = client.get("/aggregate/availability-summary")

        assert response.status_code == 200
        data = response.json()

        assert data["total_slots"] == 3
        assert len(data["slots"]) == 3
        assert "by_day" in data
        assert "by_time" in data

    def test_health_endpoint_with_healthy_services(self, client):
        """Test health endpoint when services are healthy."""
        response = client.get("/aggregate/health")

        assert response.status_code == 200
        data = response.json()

        assert data["gateway"] == "healthy"
        assert data["portal_service"] is True
        assert data["reservation_service"] is True
        assert data["all_healthy"] is True

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
                    "/aggregate/availability-summary",
                    headers={"X-Forwarded-For": "1.2.3.4"},
                )

            # Client 1.2.3.4 should be blocked
            response1 = client.get(
                "/aggregate/availability-summary",
                headers={"X-Forwarded-For": "1.2.3.4"},
            )
            assert response1.status_code == 429

            # Client 5.6.7.8 should still have quota
            response2 = client.get(
                "/aggregate/availability-summary",
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
                client.get("/aggregate/availability-summary")

            response = client.get(
                "/aggregate/availability-summary"
            )

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
                client.get("/aggregate/availability-summary")

            response = client.get(
                "/aggregate/availability-summary"
            )

            assert response.status_code == 429
            data = response.json()
            assert "detail" in data
            assert "retry_after" in data
