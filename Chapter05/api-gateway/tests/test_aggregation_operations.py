from uuid import uuid4

import pytest

from routers.aggregation import (
    fetch_aggregated_health,
    fetch_availability_summary,
    fetch_dashboard_data,
)
from services import MockPortalClient, MockReservationClient


def create_populated_reservation_client() -> (
    MockReservationClient
):
    """Create a reservation client with pre-populated slots."""
    client = MockReservationClient()
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
        client.slots[slot_id] = {
            "id": str(slot_id),
            **slot_data,
        }
    return client


class TestFetchDashboardData:
    """Tests for the fetch_dashboard_data operation."""

    @pytest.mark.asyncio
    async def test_dashboard_default_language(self):
        portal_client = MockPortalClient()
        reservation_client = create_populated_reservation_client()

        result = await fetch_dashboard_data(
            portal_client, reservation_client
        )

        assert (
            "Welcome to Babysitting Service"
            in result.welcome_content
        )
        assert result.total_available == 4
        assert len(result.available_slots) == 4

    @pytest.mark.asyncio
    async def test_dashboard_french_language(self):
        portal_client = MockPortalClient()
        reservation_client = create_populated_reservation_client()

        result = await fetch_dashboard_data(
            portal_client, reservation_client, lang="fr"
        )

        assert (
            "Bienvenue au Service de Garde"
            in result.welcome_content
        )

    @pytest.mark.asyncio
    async def test_dashboard_italian_language(self):
        portal_client = MockPortalClient()
        reservation_client = create_populated_reservation_client()

        result = await fetch_dashboard_data(
            portal_client, reservation_client, lang="it"
        )

        assert (
            "Benvenuti al Servizio di Babysitting"
            in result.welcome_content
        )

    @pytest.mark.asyncio
    async def test_dashboard_portuguese_language(self):
        portal_client = MockPortalClient()
        reservation_client = create_populated_reservation_client()

        result = await fetch_dashboard_data(
            portal_client, reservation_client, lang="pt"
        )

        assert (
            "Bem-vindo ao Serviço de Babá"
            in result.welcome_content
        )

    @pytest.mark.asyncio
    async def test_dashboard_with_name_personalization(self):
        portal_client = MockPortalClient()
        reservation_client = create_populated_reservation_client()

        result = await fetch_dashboard_data(
            portal_client, reservation_client, name="John"
        )

        assert "John" in result.welcome_content

    @pytest.mark.asyncio
    async def test_dashboard_only_returns_available_slots(self):
        portal_client = MockPortalClient()
        reservation_client = create_populated_reservation_client()

        result = await fetch_dashboard_data(
            portal_client, reservation_client
        )

        for slot in result.available_slots:
            assert slot["status"] == "available"

    @pytest.mark.asyncio
    async def test_dashboard_with_empty_slots(self):
        portal_client = MockPortalClient()
        reservation_client = MockReservationClient()

        result = await fetch_dashboard_data(
            portal_client, reservation_client
        )

        assert result.total_available == 0
        assert result.available_slots == []
        assert (
            "Welcome to Babysitting Service"
            in result.welcome_content
        )

    @pytest.mark.asyncio
    async def test_dashboard_handles_portal_failure_gracefully(
        self,
    ):
        portal_client = MockPortalClient()
        reservation_client = create_populated_reservation_client()

        # Simulate portal failure by making get_home raise an exception
        async def failing_get_home(*args, **kwargs):
            raise Exception("Portal service unavailable")

        portal_client.get_home = failing_get_home

        result = await fetch_dashboard_data(
            portal_client, reservation_client
        )

        assert "temporarily unavailable" in result.welcome_content
        assert result.total_available == 4

    @pytest.mark.asyncio
    async def test_dashboard_handles_reservation_failure_gracefully(
        self,
    ):
        portal_client = MockPortalClient()
        reservation_client = MockReservationClient()

        # Simulate reservation failure
        async def failing_list_slots(*args, **kwargs):
            raise Exception("Reservation service unavailable")

        reservation_client.list_slots = failing_list_slots

        result = await fetch_dashboard_data(
            portal_client, reservation_client
        )

        assert (
            "Welcome to Babysitting Service"
            in result.welcome_content
        )
        assert result.total_available == 0
        assert result.available_slots == []


class TestFetchAvailabilitySummary:
    """Tests for the fetch_availability_summary operation."""

    @pytest.mark.asyncio
    async def test_availability_summary_all_slots(self):
        reservation_client = create_populated_reservation_client()

        result = await fetch_availability_summary(
            reservation_client
        )

        assert result.total_slots == 4
        assert len(result.slots) == 4

    @pytest.mark.asyncio
    async def test_availability_summary_aggregates_by_day(self):
        reservation_client = create_populated_reservation_client()

        result = await fetch_availability_summary(
            reservation_client
        )

        assert "monday" in result.by_day
        assert result.by_day["monday"] == 2
        assert "tuesday" in result.by_day
        assert result.by_day["tuesday"] == 1
        assert "wednesday" in result.by_day
        assert result.by_day["wednesday"] == 1

    @pytest.mark.asyncio
    async def test_availability_summary_aggregates_by_time(self):
        reservation_client = create_populated_reservation_client()

        result = await fetch_availability_summary(
            reservation_client
        )

        assert "morning" in result.by_time
        assert result.by_time["morning"] == 1
        assert "afternoon" in result.by_time
        assert result.by_time["afternoon"] == 2
        assert "night" in result.by_time
        assert result.by_time["night"] == 1

    @pytest.mark.asyncio
    async def test_availability_summary_filter_by_week_day(self):
        reservation_client = create_populated_reservation_client()

        result = await fetch_availability_summary(
            reservation_client, week_day="monday"
        )

        assert result.total_slots == 2
        for slot in result.slots:
            assert slot["week_day"] == "monday"

    @pytest.mark.asyncio
    async def test_availability_summary_filter_by_time_slot(self):
        reservation_client = create_populated_reservation_client()

        result = await fetch_availability_summary(
            reservation_client, time_slot="morning"
        )

        # Only 1 available morning slot (Tuesday morning is pending)
        assert result.total_slots == 1
        for slot in result.slots:
            assert slot["time_slot"] == "morning"

    @pytest.mark.asyncio
    async def test_availability_summary_filter_by_both(self):
        reservation_client = create_populated_reservation_client()

        result = await fetch_availability_summary(
            reservation_client,
            week_day="monday",
            time_slot="morning",
        )

        assert result.total_slots == 1
        assert result.slots[0]["week_day"] == "monday"
        assert result.slots[0]["time_slot"] == "morning"

    @pytest.mark.asyncio
    async def test_availability_summary_no_matching_slots(self):
        reservation_client = create_populated_reservation_client()

        result = await fetch_availability_summary(
            reservation_client, week_day="sunday"
        )

        assert result.total_slots == 0
        assert result.slots == []
        assert result.by_day == {}
        assert result.by_time == {}

    @pytest.mark.asyncio
    async def test_availability_summary_excludes_non_available_slots(
        self,
    ):
        reservation_client = create_populated_reservation_client()

        result = await fetch_availability_summary(
            reservation_client
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
