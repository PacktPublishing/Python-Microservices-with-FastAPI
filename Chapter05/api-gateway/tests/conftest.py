import pytest
from uuid import uuid4

from services import MockPortalClient, MockReservationClient


@pytest.fixture
def mock_portal_client():
    """Create a fresh MockPortalClient for each test."""
    return MockPortalClient()


@pytest.fixture
def mock_reservation_client():
    """Create a fresh MockReservationClient for each test."""
    return MockReservationClient()


@pytest.fixture
def mock_reservation_client_with_slots(mock_reservation_client):
    """MockReservationClient pre-populated with test slots."""
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
        {
            "week_day": "friday",
            "time_slot": "afternoon",
            "babysitter_name": "Eve",
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
