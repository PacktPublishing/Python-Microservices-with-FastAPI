import pytest

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
