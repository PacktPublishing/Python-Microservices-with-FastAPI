import pytest
from uuid import uuid4

from services import MockPortalClient, MockReservationClient


class TestMockPortalClient:
    """Tests for MockPortalClient."""

    @pytest.mark.asyncio
    async def test_get_home_english(self, mock_portal_client):
        """Test getting English home page."""
        content = await mock_portal_client.get_home(lang="en")
        assert "Welcome to Babysitting Service" in content

    @pytest.mark.asyncio
    async def test_get_home_french(self, mock_portal_client):
        """Test getting French home page."""
        content = await mock_portal_client.get_home(lang="fr")
        assert "Bienvenue au Service de Garde" in content

    @pytest.mark.asyncio
    async def test_get_home_italian(self, mock_portal_client):
        """Test getting Italian home page."""
        content = await mock_portal_client.get_home(lang="it")
        assert "Benvenuti al Servizio di Babysitting" in content

    @pytest.mark.asyncio
    async def test_get_home_portuguese(self, mock_portal_client):
        """Test getting Portuguese home page."""
        content = await mock_portal_client.get_home(lang="pt")
        assert "Bem-vindo ao Serviço de Babá" in content

    @pytest.mark.asyncio
    async def test_get_home_with_name_personalization(self, mock_portal_client):
        """Test home page personalization with name."""
        content = await mock_portal_client.get_home(lang="en", name="John")
        assert "John" in content
        assert "Welcome to Babysitting Service" in content

    @pytest.mark.asyncio
    async def test_get_home_default_language(self, mock_portal_client):
        """Test default language is English."""
        content = await mock_portal_client.get_home()
        assert "Welcome to Babysitting Service" in content

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_portal_client):
        """Test health check when healthy."""
        assert mock_portal_client.is_healthy is True
        result = await mock_portal_client.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, mock_portal_client):
        """Test health check when unhealthy."""
        mock_portal_client.is_healthy = False
        result = await mock_portal_client.health_check()
        assert result is False


class TestMockReservationClient:
    """Tests for MockReservationClient."""

    @pytest.mark.asyncio
    async def test_list_slots_empty(self, mock_reservation_client):
        """Test listing slots when empty."""
        slots = await mock_reservation_client.list_slots()
        assert slots == []

    @pytest.mark.asyncio
    async def test_list_slots_with_data(
        self, mock_reservation_client_with_slots
    ):
        """Test listing all slots."""
        slots = await mock_reservation_client_with_slots.list_slots()
        assert len(slots) == 5

    @pytest.mark.asyncio
    async def test_list_slots_filter_by_week_day(
        self, mock_reservation_client_with_slots
    ):
        """Test filtering slots by week day."""
        slots = await mock_reservation_client_with_slots.list_slots(
            week_day="monday"
        )
        assert len(slots) == 2
        for slot in slots:
            assert slot["week_day"] == "monday"

    @pytest.mark.asyncio
    async def test_list_slots_filter_by_time_slot(
        self, mock_reservation_client_with_slots
    ):
        """Test filtering slots by time slot."""
        slots = await mock_reservation_client_with_slots.list_slots(
            time_slot="morning"
        )
        assert len(slots) == 2
        for slot in slots:
            assert slot["time_slot"] == "morning"

    @pytest.mark.asyncio
    async def test_list_slots_filter_by_both(
        self, mock_reservation_client_with_slots
    ):
        """Test filtering slots by both week day and time slot."""
        slots = await mock_reservation_client_with_slots.list_slots(
            week_day="monday",
            time_slot="morning",
        )
        assert len(slots) == 1
        assert slots[0]["week_day"] == "monday"
        assert slots[0]["time_slot"] == "morning"

    @pytest.mark.asyncio
    async def test_list_slots_no_match(
        self, mock_reservation_client_with_slots
    ):
        """Test filtering with no matching slots."""
        slots = await mock_reservation_client_with_slots.list_slots(
            week_day="sunday"
        )
        assert slots == []

    @pytest.mark.asyncio
    async def test_reserve_slot_success(
        self, mock_reservation_client_with_slots
    ):
        """Test successful slot reservation."""
        # Find an available slot - get the UUID key directly
        available_slot_id = next(
            slot_id
            for slot_id, slot in mock_reservation_client_with_slots.slots.items()
            if slot["status"] == "available"
        )

        result = await mock_reservation_client_with_slots.reserve_slot(
            slot_id=available_slot_id,
            parent_email="parent@example.com",
            description="Need babysitter for dinner",
        )

        assert result["status"] == "pending"
        assert result["parent_email"] == "parent@example.com"
        assert result["description"] == "Need babysitter for dinner"

    @pytest.mark.asyncio
    async def test_reserve_slot_not_found(self, mock_reservation_client):
        """Test reserving non-existent slot."""
        with pytest.raises(ValueError, match="not found"):
            await mock_reservation_client.reserve_slot(
                slot_id=uuid4(),
                parent_email="parent@example.com",
            )

    @pytest.mark.asyncio
    async def test_reserve_slot_not_available(
        self, mock_reservation_client_with_slots
    ):
        """Test reserving a slot that is not available."""
        # Find a pending slot - get UUID key directly
        pending_slot_id = next(
            slot_id
            for slot_id, slot in mock_reservation_client_with_slots.slots.items()
            if slot["status"] == "pending"
        )

        with pytest.raises(ValueError, match="not available"):
            await mock_reservation_client_with_slots.reserve_slot(
                slot_id=pending_slot_id,
                parent_email="parent@example.com",
            )

    @pytest.mark.asyncio
    async def test_reserve_slot_default_description(
        self, mock_reservation_client_with_slots
    ):
        """Test reservation with default empty description."""
        # Get UUID key directly
        available_slot_id = next(
            slot_id
            for slot_id, slot in mock_reservation_client_with_slots.slots.items()
            if slot["status"] == "available"
        )

        result = await mock_reservation_client_with_slots.reserve_slot(
            slot_id=available_slot_id,
            parent_email="parent@example.com",
        )

        assert result["description"] == ""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_reservation_client):
        """Test health check when healthy."""
        assert mock_reservation_client.is_healthy is True
        result = await mock_reservation_client.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, mock_reservation_client):
        """Test health check when unhealthy."""
        mock_reservation_client.is_healthy = False
        result = await mock_reservation_client.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_slot_state_mutation(self, mock_reservation_client):
        """Test that reserving a slot mutates its state."""
        slot_id = uuid4()
        mock_reservation_client.slots[slot_id] = {
            "id": str(slot_id),
            "week_day": "monday",
            "time_slot": "morning",
            "babysitter_name": "Test",
            "status": "available",
        }

        # Reserve the slot
        await mock_reservation_client.reserve_slot(
            slot_id=slot_id,
            parent_email="test@example.com",
        )

        # Verify state changed
        assert mock_reservation_client.slots[slot_id]["status"] == "pending"

        # Cannot reserve again
        with pytest.raises(ValueError, match="not available"):
            await mock_reservation_client.reserve_slot(
                slot_id=slot_id,
                parent_email="another@example.com",
            )
