import pytest
from seeders import SlotSeeder

from infrastructure.in_memory_slot_repository import (
    InMemorySlotRepository,
)


@pytest.fixture
def empty_repository():
    """Fixture providing an empty in-memory repository"""
    return InMemorySlotRepository()


@pytest.fixture
def seeded_repository():
    """Fixture providing a repository with sample data"""
    repo = InMemorySlotRepository()
    SlotSeeder.seed(repo)
    return repo
