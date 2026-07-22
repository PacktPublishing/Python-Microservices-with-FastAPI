import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIASGIMiddleware

from rate_limiter import get_client_ip
from services import MockPortalClient, MockReservationClient


@pytest.fixture
def mock_portal_client():
    """Create a fresh MockPortalClient for each test."""
    return MockPortalClient()


@pytest.fixture
def mock_reservation_client():
    """Create a fresh MockReservationClient without prefilled slots."""
    return MockReservationClient()


@pytest.fixture
def mock_reservation_client_with_slots():
    """Create a fresh MockReservationClient with prefilled slots."""
    return MockReservationClient(prefill=True)


@pytest.fixture
def limiter():
    """Create a limiter instance for testing."""
    return Limiter(
        key_func=get_client_ip,
        headers_enabled=True,
    )


@pytest.fixture
def app_with_limiter(limiter):
    """Create a basic FastAPI app with rate limiting.

    Provides a simple rate-limited app with /test (2/min) and
    /unlimited endpoints for testing rate limiter behavior.
    """
    app = FastAPI()
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(
        _request: Request, _exc: RateLimitExceeded
    ):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "retry_after": "60",
            },
            headers={"Retry-After": "60"},
        )

    app.add_middleware(
        SlowAPIASGIMiddleware  # ty: ignore[invalid-argument-type]
    )

    @app.get("/test")
    @limiter.limit("2/minute")
    async def test_endpoint(
        request: Request, response: Response
    ):
        _ = request, response
        return {"message": "ok"}

    @app.get("/unlimited")
    async def unlimited_endpoint():
        return {"message": "unlimited"}

    return app


@pytest.fixture
def rate_limited_client(app_with_limiter):
    """Create a test client for the basic rate-limited app."""
    with TestClient(app_with_limiter) as client:
        yield client
