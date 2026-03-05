from abc import ABC, abstractmethod
from uuid import UUID

from .entities import AvailabilitySlot
from .value_objects import TimeSlot, WeekDay


class AvailabilitySlotRepository(ABC):
    """Repository interface for AvailabilitySlot aggregate root"""

    @abstractmethod
    def save(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        """Save or update a slot"""

    @abstractmethod
    def find_by_id(
        self, slot_id: UUID
    ) -> AvailabilitySlot | None:
        """Find a slot by its ID"""

    @abstractmethod
    def find_available_slots(
        self,
        week_day: WeekDay | None = None,
        time_slot: TimeSlot | None = None,
    ) -> list[AvailabilitySlot]:
        """Find all available slots, optionally filtered by day and time"""

    @abstractmethod
    def delete(self, slot_id: UUID) -> bool:
        """Delete a slot by ID. Returns True if deleted, False if not found"""
