from dataclasses import field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic.dataclasses import dataclass

from .exceptions import (
    SlotNotAvailableException,
    SlotNotReservedException,
)
from .value_objects import (
    BabysitterInfo,
    ReservationRequest,
    SlotStatus,
    TimeSlot,
    WeekDay,
)


@dataclass(kw_only=True)
class AvailabilitySlot:
    """Aggregate Root for babysitter availability slots"""

    # Slot definition
    week_day: WeekDay
    time_slot: TimeSlot
    babysitter: BabysitterInfo

    # Identity
    id: UUID = field(default_factory=uuid4)

    # State
    status: SlotStatus = field(default=SlotStatus.AVAILABLE)

    # Reservation details (populated when reserved)
    reservation: ReservationRequest | None = field(default=None)
    reserved_at: datetime | None = field(default=None)
    confirmed_at: datetime | None = field(default=None)

    # Domain methods

    def reserve(
        self, reservation_request: ReservationRequest
    ) -> None:
        """Reserve this slot for a parent"""
        if self.status != SlotStatus.AVAILABLE:
            raise SlotNotAvailableException(
                f"Slot {self.id} is not available (current status: {self.status.value})"
            )

        self.status = SlotStatus.RESERVED
        self.reservation = reservation_request
        self.reserved_at = datetime.now(UTC)

    def confirm(self) -> None:
        """Babysitter confirms the reservation"""
        if self.status != SlotStatus.RESERVED:
            raise SlotNotReservedException(
                f"Cannot confirm slot {self.id} - not in reserved state"
            )

        self.status = SlotStatus.CONFIRMED
        self.confirmed_at = datetime.now(UTC)

    def refuse(self) -> None:
        """Babysitter refuses the reservation - slot becomes available again"""
        if self.status != SlotStatus.RESERVED:
            raise SlotNotReservedException(
                f"Cannot refuse slot {self.id} - not in reserved state"
            )

        # Reset to available and clear reservation data
        self.status = SlotStatus.AVAILABLE
        self.reservation = None
        self.reserved_at = None
