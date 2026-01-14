from copy import deepcopy
from typing import Dict, List
from uuid import UUID

from domain.entities import AvailabilitySlot
from domain.repositories import AvailabilitySlotRepository
from domain.value_objects import SlotStatus, TimeSlot, WeekDay


class InMemorySlotRepository(AvailabilitySlotRepository):
    """In-memory implementation of AvailabilitySlotRepository for testing/demo"""

    def __init__(self):
        self._storage: Dict[UUID, AvailabilitySlot] = {}

    def save(self, slot: AvailabilitySlot) -> AvailabilitySlot:
        """Save or update a slot"""
        # Deep copy to simulate persistence (avoid reference sharing)
        self._storage[slot.id] = deepcopy(slot)
        return deepcopy(self._storage[slot.id])

    def find_by_id(
        self, slot_id: UUID
    ) -> AvailabilitySlot | None:
        """Find a slot by its ID"""
        slot = self._storage.get(slot_id)
        # Return a deep copy to prevent external modifications
        return deepcopy(slot) if slot else None

    def find_available_slots(
        self,
        week_day: WeekDay | None = None,
        time_slot: TimeSlot | None = None,
    ) -> List[AvailabilitySlot]:
        """Find all available slots, optionally filtered by day and time"""
        results = []

        for slot in self._storage.values():
            # Check if slot is available
            if slot.status != SlotStatus.AVAILABLE:
                continue

            # Apply filters if provided
            if week_day and slot.week_day != week_day:
                continue

            if time_slot and slot.time_slot != time_slot:
                continue

            results.append(deepcopy(slot))

        return results

    def delete(self, slot_id: UUID) -> bool:
        """Delete a slot by ID. Returns True if deleted, False if not found"""
        if slot_id in self._storage:
            del self._storage[slot_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all slots (useful for testing)"""
        self._storage.clear()
