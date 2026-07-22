from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rate_limiter import limiter
from routers import aggregation_router
from services import MockPortalClient, MockReservationClient

# Disable rate limiter for unit tests
limiter.enabled = False


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
            "week_day": "tuesday",
            "time_slot": "afternoon",
            "babysitter_name": "Diana",
            "status": "available",
        },
        {
            "week_day": "wednesday",
            "time_slot": "night",
            "babysitter_name": "Eve",
            "status": "available",
        },
        {
            "week_day": "friday",
            "time_slot": "afternoon",
            "babysitter_name": "Frank",
            "status": "confirmed",
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
def client(mock_portal_client, populated_reservation_client):
    """Create test client with mock clients using lifespan."""

    @asynccontextmanager
    async def test_lifespan(
        _app: FastAPI,
    ) -> AsyncGenerator[dict]:
        yield {
            "portal_client": mock_portal_client,
            "reservation_client": populated_reservation_client,
        }

    app = FastAPI(lifespan=test_lifespan)
    app.include_router(aggregation_router)

    with TestClient(app) as test_client:
        yield test_client


class TestAvailabilitySummaryEndpoint:
    """Tests for GET /aggregate/availability-summary."""

    def test_availability_summary_all(self, client):
        """Test availability summary without filters."""
        response = client.get("/aggregate/availability-summary")

        assert response.status_code == 200
        data = response.json()

        assert "total_slots" in data
        assert "by_day" in data
        assert "by_time" in data

        assert "slots" in data

        # Only available slots counted
        assert data["total_slots"] == 4

    def test_availability_summary_by_day(self, client):
        """Test availability aggregation by day."""
        response = client.get("/aggregate/availability-summary")

        assert response.status_code == 200
        data = response.json()

        # Check by_day aggregation
        assert "monday" in data["by_day"]
        assert (
            data["by_day"]["monday"] == 2
        )  # 2 available on Monday

    def test_availability_summary_by_time(self, client):
        """Test availability aggregation by time slot."""
        response = client.get("/aggregate/availability-summary")

        assert response.status_code == 200
        data = response.json()

        # Check by_time aggregation
        assert "morning" in data["by_time"]
        assert "afternoon" in data["by_time"]
        assert "night" in data["by_time"]

    def test_availability_summary_filter_by_day(self, client):
        """Test filtering availability by week day."""
        response = client.get(
            "/aggregate/availability-summary?week_day=monday"
        )

        assert response.status_code == 200
        data = response.json()

        # Should only return Monday slots
        for slot in data["slots"]:
            assert slot["week_day"] == "monday"

    def test_availability_summary_filter_by_time(self, client):
        """Test filtering availability by time slot."""
        response = client.get(
            "/aggregate/availability-summary?time_slot=morning"
        )

        assert response.status_code == 200
        data = response.json()

        for slot in data["slots"]:
            assert slot["time_slot"] == "morning"

    def test_availability_summary_combined_filters(self, client):
        """Test filtering by both day and time."""
        response = client.get(
            "/aggregate/availability-summary"
            "?week_day=monday&time_slot=morning"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_slots"] == 1
        assert data["slots"][0]["week_day"] == "monday"
        assert data["slots"][0]["time_slot"] == "morning"

    def test_availability_summary_no_results(self, client):
        """Test summary with no matching slots."""
        response = client.get(
            "/aggregate/availability-summary?week_day=sunday"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_slots"] == 0
        assert data["slots"] == []
        assert data["by_day"] == {}
        assert data["by_time"] == {}


class TestHealthEndpoint:
    """Tests for GET /aggregate/health."""

    def test_health_all_healthy(self, client):
        """Test health when all services healthy."""
        response = client.get("/aggregate/health")

        assert response.status_code == 200
        data = response.json()

        assert data["gateway"] == "healthy"
        assert data["portal_service"] is True
        assert data["reservation_service"] is True
        assert data["all_healthy"] is True
