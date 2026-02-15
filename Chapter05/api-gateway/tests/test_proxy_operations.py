from uuid import UUID, uuid4

import pytest

from routers.proxy import (
    fetch_portal_home,
    get_all_available_slots,
    make_reservation,
)
from services import MockPortalClient, MockReservationClient


class TestFetchPortalHome:
    """Tests for the fetch_portal_home operation."""

    @pytest.mark.asyncio
    async def test_fetch_portal_home_english(self):
        client = MockPortalClient()
        result = await fetch_portal_home(client, lang="en")
        assert "Welcome to Babysitting Service" in result

    @pytest.mark.asyncio
    async def test_fetch_portal_home_french(self):
        client = MockPortalClient()
        result = await fetch_portal_home(client, lang="fr")
        assert "Bienvenue au Service de Garde" in result

    @pytest.mark.asyncio
    async def test_fetch_portal_home_italian(self):
        client = MockPortalClient()
        result = await fetch_portal_home(client, lang="it")
        assert "Benvenuti al Servizio di Babysitting" in result

    @pytest.mark.asyncio
    async def test_fetch_portal_home_portuguese(self):
        client = MockPortalClient()
        result = await fetch_portal_home(client, lang="pt")
        assert "Bem-vindo ao Serviço de Babá" in result

    @pytest.mark.asyncio
    async def test_fetch_portal_home_with_name(self):
        client = MockPortalClient()
        result = await fetch_portal_home(
            client, lang="en", name="John"
        )
        assert "John" in result
        assert "Welcome to Babysitting Service" in result

    @pytest.mark.asyncio
    async def test_fetch_portal_home_default_language(self):
        client = MockPortalClient()
        result = await fetch_portal_home(client)
        assert "Welcome to Babysitting Service" in result


class TestFetchAllReservations:
    """Tests for the fetch_all_reservations operation."""

    @pytest.mark.asyncio
    async def test_fetch_all_reservations_empty(self):
        client = MockReservationClient()
        result = await get_all_available_slots(client)
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_all_reservations_with_slots(self):
        client = MockReservationClient(prefill=True)
        result = await get_all_available_slots(client)
        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_fetch_all_reservations_filter_by_week_day(
        self,
    ):
        client = MockReservationClient(prefill=True)
        result = await get_all_available_slots(
            client, week_day="monday"
        )
        assert len(result) == 2
        for slot in result:
            assert slot["week_day"] == "monday"

    @pytest.mark.asyncio
    async def test_fetch_all_reservations_filter_by_time_slot(
        self,
    ):
        client = MockReservationClient(prefill=True)
        result = await get_all_available_slots(
            client, time_slot="morning"
        )
        assert len(result) == 1
        for slot in result:
            assert slot["time_slot"] == "morning"

    @pytest.mark.asyncio
    async def test_fetch_all_reservations_filter_by_both(self):
        client = MockReservationClient(prefill=True)
        result = await get_all_available_slots(
            client, week_day="monday", time_slot="morning"
        )
        assert len(result) == 1
        assert result[0]["week_day"] == "monday"
        assert result[0]["time_slot"] == "morning"

    @pytest.mark.asyncio
    async def test_fetch_all_reservations_no_matches(self):
        client = MockReservationClient(prefill=True)
        result = await get_all_available_slots(
            client, week_day="sunday"
        )
        assert result == []


class TestMakeReservation:
    """Tests for the make_reservation operation."""

    @pytest.mark.asyncio
    async def test_make_reservation_success(self):
        client = MockReservationClient(prefill=True)
        slots = await client.list_available_slots()
        available_slot = next(
            s for s in slots if s["status"] == "available"
        )
        slot_id = UUID(available_slot["id"])

        result = await make_reservation(
            client,
            slot_id=slot_id,
            parent_email="parent@example.com",
            description="Need babysitter for the afternoon",
        )

        assert result["status"] == "pending"
        assert result["parent_email"] == "parent@example.com"
        assert (
            result["description"]
            == "Need babysitter for the afternoon"
        )

    @pytest.mark.asyncio
    async def test_make_reservation_slot_not_found(self):
        client = MockReservationClient()
        non_existent_slot_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            await make_reservation(
                client,
                slot_id=non_existent_slot_id,
                parent_email="parent@example.com",
            )

    @pytest.mark.asyncio
    async def test_make_reservation_slot_not_available(self):
        client = MockReservationClient(prefill=True)
        slots = client.slots.values()
        pending_slot = next(
            s for s in slots if s["status"] == "pending"
        )
        slot_id = UUID(pending_slot["id"])

        with pytest.raises(ValueError, match="not available"):
            await make_reservation(
                client,
                slot_id=slot_id,
                parent_email="parent@example.com",
            )

    @pytest.mark.asyncio
    async def test_make_reservation_without_description(self):
        client = MockReservationClient(prefill=True)
        slots = await client.list_available_slots()
        available_slot = next(
            s for s in slots if s["status"] == "available"
        )
        slot_id = UUID(available_slot["id"])

        result = await make_reservation(
            client,
            slot_id=slot_id,
            parent_email="parent@example.com",
        )

        assert result["status"] == "pending"
        assert result["parent_email"] == "parent@example.com"
        assert result["description"] == ""

    @pytest.mark.asyncio
    async def test_make_reservation_changes_slot_status(self):
        client = MockReservationClient(prefill=True)
        slots = await client.list_available_slots()
        available_slot = next(
            s for s in slots if s["status"] == "available"
        )
        slot_id = UUID(available_slot["id"])

        await make_reservation(
            client,
            slot_id=slot_id,
            parent_email="parent@example.com",
        )

        # Verify slot status changed
        updated_slots = client.slots.values()
        updated_slot = next(
            s for s in updated_slots if s["id"] == str(slot_id)
        )
        assert updated_slot["status"] == "pending"
