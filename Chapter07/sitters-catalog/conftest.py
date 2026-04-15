"""
Shared test fixtures used across all test modules.
"""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from features.create_babysitter.route import (
    router as create_router,
)
from features.deactivate_babysitter.route import (
    router as deactivate_router,
)
from features.delete_babysitter.route import (
    router as delete_router,
)
from features.get_babysitter.route import router as get_router
from features.get_featured.route import router as featured_router
from features.health.route import router as health_router
from features.list_babysitters.route import router as list_router
from features.update_babysitter.route import (
    router as update_router,
)
from shared.domain.value_objects import (
    AvailabilitySlot,
    ContactInfo,
    Location,
)
from shared.infrastructure import TinyDBRepository

# ── Common IDs ──────────────────────────────────────────────

SAMPLE_OBJECT_ID = ObjectId()
SAMPLE_ID = str(SAMPLE_OBJECT_ID)

# ── Reusable value-object fixtures ──────────────────────────


@pytest.fixture
def sample_location() -> Location:
    return Location(
        city="Paris",
        country="France",
        latitude=48.8566,
        longitude=2.3522,
    )


@pytest.fixture
def sample_contact() -> ContactInfo:
    return ContactInfo(
        email="alice@example.com", phone="+33612345678"
    )


@pytest.fixture
def sample_availability() -> list[AvailabilitySlot]:
    return [
        AvailabilitySlot(day="Monday", from_hour=8, to_hour=18),
        AvailabilitySlot(
            day="Wednesday", from_hour=9, to_hour=17
        ),
    ]


# ── Mock BabysitterDocument factory ─────────────────────────


def make_mock_doc(
    *,
    id: ObjectId | None = None,
    is_active: bool = True,
    location: Location | None = None,
    contact: ContactInfo | None = None,
) -> MagicMock:
    """Fully-populated MagicMock mimicking BabysitterDocument."""
    doc = MagicMock()
    doc.id = id or SAMPLE_OBJECT_ID
    doc.first_name = "Alice"
    doc.last_name = "Dupont"
    doc.age = 28
    doc.bio = "Experienced nanny"
    doc.hourly_rate = 18.50
    doc.years_of_experience = 5
    doc.languages = ["English", "French"]
    doc.certifications = ["First Aid", "CPR"]
    doc.availability = [
        AvailabilitySlot(day="Monday", from_hour=8, to_hour=18)
    ]
    doc.contact = contact or ContactInfo(
        email="alice@example.com"
    )
    doc.location = location or Location(
        city="Paris", country="France"
    )
    doc.is_active = is_active
    doc.created_at = datetime.now(UTC)
    doc.updated_at = datetime.now(UTC)
    return doc


# ── Integration test fixtures ──────────────────────────────────


@pytest.fixture
def repository() -> Iterator[TinyDBRepository]:
    """Create an in-memory TinyDB repository for testing."""
    repo = TinyDBRepository(in_memory=True)
    yield repo
    repo._collection.truncate()


@pytest.fixture
def app(repository: TinyDBRepository) -> FastAPI:
    """Create test FastAPI app with TinyDB repository."""

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[dict]:
        yield {"repository": repository}

    test_app = FastAPI(lifespan=lifespan)

    test_app.include_router(health_router)
    test_app.include_router(create_router)
    test_app.include_router(featured_router)
    test_app.include_router(list_router)
    test_app.include_router(get_router)
    test_app.include_router(update_router)
    test_app.include_router(delete_router)
    test_app.include_router(deactivate_router)

    return test_app


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Create test client for the app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_babysitter_data() -> dict:
    """Valid babysitter creation payload."""
    return {
        "first_name": "Alice",
        "last_name": "Dupont",
        "age": 28,
        "bio": "Experienced nanny with 5 years of experience",
        "hourly_rate": 18.50,
        "years_of_experience": 5,
        "languages": ["English", "French"],
        "certifications": ["First Aid", "CPR"],
        "availability": [
            {"day": "Monday", "from_hour": 8, "to_hour": 18},
            {"day": "Wednesday", "from_hour": 9, "to_hour": 17},
        ],
        "contact": {
            "email": "alice@example.com",
            "phone": "+33612345678",
        },
        "location": {
            "city": "Paris",
            "country": "France",
            "latitude": 48.8566,
            "longitude": 2.3522,
        },
    }


@pytest.fixture
def another_babysitter_data() -> dict:
    """Second babysitter for testing lists and filters."""
    return {
        "first_name": "Bob",
        "last_name": "Martin",
        "age": 35,
        "bio": "Professional childcare specialist",
        "hourly_rate": 25.00,
        "years_of_experience": 10,
        "languages": ["English", "Spanish"],
        "certifications": ["First Aid", "Child Psychology"],
        "availability": [
            {"day": "Tuesday", "from_hour": 9, "to_hour": 18},
        ],
        "contact": {"email": "bob@example.com"},
        "location": {"city": "Lyon", "country": "France"},
    }
