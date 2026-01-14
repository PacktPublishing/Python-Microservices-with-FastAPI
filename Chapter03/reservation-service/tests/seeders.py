from typing import List
from uuid import UUID

from domain.entities import AvailabilitySlot
from domain.repositories import AvailabilitySlotRepository
from domain.value_objects import (
    BabysitterInfo,
    TimeSlot,
    WeekDay,
)


class SlotSeeder:
    """Seed data generator for availability slots"""

    SAMPLE_BABYSITTERS = [
        "Maria Rodriguez",
        "Sophie Dubois",
        "Emma Johnson",
        "Anna Kowalski",
    ]

    # Configuration for slots: (week_day, time_slot, babysitter_index)
    SLOT_CONFIGS = [
        # Monday
        (WeekDay.MONDAY, TimeSlot.MORNING, 0),
        (WeekDay.MONDAY, TimeSlot.AFTERNOON, 1),
        (WeekDay.MONDAY, TimeSlot.NIGHT, 2),
        # Tuesday
        (WeekDay.TUESDAY, TimeSlot.MORNING, 1),
        (WeekDay.TUESDAY, TimeSlot.AFTERNOON, 3),
        (WeekDay.TUESDAY, TimeSlot.NIGHT, 0),
        # Wednesday
        (WeekDay.WEDNESDAY, TimeSlot.MORNING, 2),
        (WeekDay.WEDNESDAY, TimeSlot.AFTERNOON, 0),
        (WeekDay.WEDNESDAY, TimeSlot.NIGHT, 3),
        # Thursday
        (WeekDay.THURSDAY, TimeSlot.MORNING, 3),
        (WeekDay.THURSDAY, TimeSlot.AFTERNOON, 2),
        (WeekDay.THURSDAY, TimeSlot.NIGHT, 1),
        # Friday
        (WeekDay.FRIDAY, TimeSlot.MORNING, 3),
        (WeekDay.FRIDAY, TimeSlot.AFTERNOON, 1),
        (WeekDay.FRIDAY, TimeSlot.NIGHT, 2),
        # Saturday
        (WeekDay.SATURDAY, TimeSlot.MORNING, 1),
        (WeekDay.SATURDAY, TimeSlot.AFTERNOON, 3),
        (WeekDay.SATURDAY, TimeSlot.NIGHT, 0),
        # Sunday
        (WeekDay.SUNDAY, TimeSlot.MORNING, 2),
        (WeekDay.SUNDAY, TimeSlot.AFTERNOON, 0),
        (WeekDay.SUNDAY, TimeSlot.NIGHT, 3),
    ]

    @classmethod
    def seed(
        cls, repository: AvailabilitySlotRepository
    ) -> List[UUID]:
        """
        Populate repository with sample data for testing/demo.
        Returns list of created slot IDs.
        """
        created_ids = []

        for (
            week_day,
            time_slot,
            babysitter_idx,
        ) in cls.SLOT_CONFIGS:
            slot = AvailabilitySlot(
                week_day=week_day,
                time_slot=time_slot,
                babysitter=BabysitterInfo(
                    name=cls.SAMPLE_BABYSITTERS[babysitter_idx]
                ),
            )
            saved_slot = repository.save(slot)
            created_ids.append(saved_slot.id)

        return created_ids
