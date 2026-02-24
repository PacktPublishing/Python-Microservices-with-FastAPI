import pytest

from routers.aggregation import (
    fetch_aggregated_health,
    fetch_availability_summary,
)
from services import MockPortalClient, MockReservationClient


@pytest.fixture
def populated_reservation_client() -> MockReservationClient:
    """Create a reservation client with pre-populated slots."""
    return MockReservationClient(prefill=True)


class TestFetchAvailabilitySummary:
    """Tests for the fetch_availability_summary operation."""

    @pytest.mark.asyncio
    async def test_availability_summary_all_slots(
        self, populated_reservation_client
    ):
        result = await fetch_availability_summary(
            populated_reservation_client
        )

        # Prefilled data has 4 available slots (Alice, Bob, Diana, Eve)
        assert result.total_slots == 4
        assert len(result.slots) == 4

    @pytest.mark.asyncio
    async def test_availability_summary_aggregates_by_day(
        self, populated_reservation_client
    ):
        result = await fetch_availability_summary(
            populated_reservation_client
        )

        assert "monday" in result.by_day
        assert result.by_day["monday"] == 2
        assert "wednesday" in result.by_day
        assert result.by_day["wednesday"] == 1
        assert "friday" in result.by_day
        assert result.by_day["friday"] == 1

    @pytest.mark.asyncio
    async def test_availability_summary_aggregates_by_time(
        self, populated_reservation_client
    ):
        result = await fetch_availability_summary(
            populated_reservation_client
        )

        assert "morning" in result.by_time
        assert result.by_time["morning"] == 1
        assert "afternoon" in result.by_time
        assert result.by_time["afternoon"] == 2
        assert "night" in result.by_time
        assert result.by_time["night"] == 1

    @pytest.mark.asyncio
    async def test_availability_summary_filter_by_week_day(
        self, populated_reservation_client
    ):
        result = await fetch_availability_summary(
            populated_reservation_client, week_day="monday"
        )

        assert result.total_slots == 2
        for slot in result.slots:
            assert slot["week_day"] == "monday"

    @pytest.mark.asyncio
    async def test_availability_summary_filter_by_time_slot(
        self, populated_reservation_client
    ):
        result = await fetch_availability_summary(
            populated_reservation_client, time_slot="morning"
        )

        # Only 1 available morning slot (Tuesday morning is pending)
        assert result.total_slots == 1
        for slot in result.slots:
            assert slot["time_slot"] == "morning"

    @pytest.mark.asyncio
    async def test_availability_summary_filter_by_both(
        self, populated_reservation_client
    ):
        result = await fetch_availability_summary(
            populated_reservation_client,
            week_day="monday",
            time_slot="morning",
        )

        assert result.total_slots == 1
        assert result.slots[0]["week_day"] == "monday"
        assert result.slots[0]["time_slot"] == "morning"

    @pytest.mark.asyncio
    async def test_availability_summary_no_matching_slots(
        self, populated_reservation_client
    ):
        result = await fetch_availability_summary(
            populated_reservation_client, week_day="sunday"
        )

        assert result.total_slots == 0
        assert result.slots == []
        assert result.by_day == {}
        assert result.by_time == {}

    @pytest.mark.asyncio
    async def test_availability_summary_excludes_non_available_slots(
        self, populated_reservation_client
    ):
        result = await fetch_availability_summary(
            populated_reservation_client
        )

        # Should exclude pending and confirmed slots
        for slot in result.slots:
            assert slot["status"] == "available"

    @pytest.mark.asyncio
    async def test_availability_summary_empty_client(self):
        reservation_client = MockReservationClient()

        result = await fetch_availability_summary(
            reservation_client
        )

        assert result.total_slots == 0
        assert result.slots == []
        assert result.by_day == {}
        assert result.by_time == {}


class TestFetchAggregatedHealth:
    """Tests for the fetch_aggregated_health operation."""

    @pytest.mark.asyncio
    async def test_health_all_services_healthy(self):
        portal_client = MockPortalClient()
        reservation_client = MockReservationClient()

        result = await fetch_aggregated_health(
            portal_client, reservation_client
        )

        assert result.gateway == "healthy"
        assert result.portal_service is True
        assert result.reservation_service is True
        assert result.all_healthy is True

    @pytest.mark.asyncio
    async def test_health_portal_unhealthy(self):
        portal_client = MockPortalClient()
        portal_client.is_healthy = False
        reservation_client = MockReservationClient()

        result = await fetch_aggregated_health(
            portal_client, reservation_client
        )

        assert result.gateway == "healthy"
        assert result.portal_service is False
        assert result.reservation_service is True
        assert result.all_healthy is False

    @pytest.mark.asyncio
    async def test_health_reservation_unhealthy(self):
        portal_client = MockPortalClient()
        reservation_client = MockReservationClient()
        reservation_client.is_healthy = False

        result = await fetch_aggregated_health(
            portal_client, reservation_client
        )

        assert result.gateway == "healthy"
        assert result.portal_service is True
        assert result.reservation_service is False
        assert result.all_healthy is False

    @pytest.mark.asyncio
    async def test_health_both_services_unhealthy(self):
        portal_client = MockPortalClient()
        portal_client.is_healthy = False
        reservation_client = MockReservationClient()
        reservation_client.is_healthy = False

        result = await fetch_aggregated_health(
            portal_client, reservation_client
        )

        assert result.gateway == "healthy"
        assert result.portal_service is False
        assert result.reservation_service is False
        assert result.all_healthy is False

    @pytest.mark.asyncio
    async def test_health_gateway_always_healthy(self):
        portal_client = MockPortalClient()
        portal_client.is_healthy = False
        reservation_client = MockReservationClient()
        reservation_client.is_healthy = False

        result = await fetch_aggregated_health(
            portal_client, reservation_client
        )

        # Gateway itself is always reported as healthy
        assert result.gateway == "healthy"
