from domain.entities import AvailabilitySlot
from .dtos import SlotResponse


class SlotMapper:
    """Mapper to convert domain entities to DTOs"""

    @staticmethod
    def to_response(slot: AvailabilitySlot) -> SlotResponse:
        """Convert AvailabilitySlot entity to SlotResponse DTO"""
        if slot.reservation is not None:
            reservation_email = slot.reservation.email
            reservation_description = slot.reservation.description
        else:
            reservation_email = None
            reservation_description = None

        return SlotResponse(
            id=slot.id,
            week_day=slot.week_day,
            time_slot=slot.time_slot,
            babysitter_name=slot.babysitter.name,
            status=slot.status.value,
            reservation_email=reservation_email,
            reservation_description=reservation_description,
            reserved_at=slot.reserved_at,
            confirmed_at=slot.confirmed_at,
        )
