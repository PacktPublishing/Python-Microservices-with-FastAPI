from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.value_objects import TimeSlot, WeekDay


@dataclass
class CreateSlotRequest:
    """DTO for creating a new availability slot"""

    week_day: WeekDay
    time_slot: TimeSlot
    babysitter_name: str


@dataclass
class ReserveSlotRequest:
    """DTO for reserving a slot"""

    slot_id: UUID
    parent_email: str
    description: str = ""


@dataclass
class ConfirmSlotRequest:
    """DTO for confirming a reservation"""

    slot_id: UUID


@dataclass
class RefuseSlotRequest:
    """DTO for refusing a reservation"""

    slot_id: UUID


@dataclass
class SlotResponse:
    """DTO for returning slot information"""

    id: UUID
    week_day: WeekDay
    time_slot: TimeSlot
    babysitter_name: str
    status: str
    reservation_email: str | None
    reservation_description: str | None
    reserved_at: datetime | None = None
    confirmed_at: datetime | None = None


@dataclass
class ListAvailableSlotsRequest:
    """DTO for querying available slots"""

    week_day: WeekDay | None = None
    time_slot: TimeSlot | None = None
