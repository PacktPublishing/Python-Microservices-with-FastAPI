from typing import List
from pydantic_core import ValidationError
from .exceptions import SlotNotFoundException
from domain.entities import AvailabilitySlot
from domain.repositories import AvailabilitySlotRepository
from domain.value_objects import (
    BabysitterInfo,
    ReservationRequest,
)
from domain.exceptions import (
    SlotNotAvailableException,
    SlotNotReservedException,
)

from .dtos import (
    CreateSlotRequest,
    ReserveSlotRequest,
    ConfirmSlotRequest,
    RefuseSlotRequest,
    SlotResponse,
    ListAvailableSlotsRequest,
)
from .exceptions import (
    InvalidInputException,
)
from .mappers import SlotMapper


class CreateAvailabilitySlotUseCase:
    """Use case for creating a new availability slot"""

    def __init__(self, repository: AvailabilitySlotRepository):
        self.repository = repository

    def execute(self, request: CreateSlotRequest) -> SlotResponse:
        # Validate and convert input
        try:
            slot = AvailabilitySlot(
                week_day=request.week_day,
                time_slot=request.time_slot,
                babysitter=BabysitterInfo(
                    name=request.babysitter_name
                ),
            )
        except (ValidationError, ValueError) as e:
            raise InvalidInputException(
                f"Invalid input: {str(e)}"
            )

        # Persist
        saved_slot = self.repository.save(slot)

        # Return DTO
        return SlotMapper.to_response(saved_slot)


class ReserveSlotUseCase:
    """Use case for reserving an availability slot"""

    def __init__(self, repository: AvailabilitySlotRepository):
        self.repository = repository

    def execute(
        self, request: ReserveSlotRequest
    ) -> SlotResponse:
        # Find slot
        slot = self.repository.find_by_id(request.slot_id)
        if not slot:
            raise SlotNotFoundException(
                f"Slot {request.slot_id} not found"
            )

        # Create reservation request
        try:
            reservation = ReservationRequest(
                email=request.parent_email,
                description=request.description,
            )
            slot.reserve(reservation)

        except (SlotNotAvailableException, ValueError) as e:
            raise InvalidInputException(str(e))

        # Persist changes
        saved_slot = self.repository.save(slot)

        # Return DTO
        return SlotMapper.to_response(saved_slot)


class ConfirmReservationUseCase:
    """Use case for babysitter confirming a reservation"""

    def __init__(self, repository: AvailabilitySlotRepository):
        self.repository = repository

    def execute(
        self, request: ConfirmSlotRequest
    ) -> SlotResponse:
        # Find slot
        slot = self.repository.find_by_id(request.slot_id)
        if not slot:
            raise SlotNotFoundException(
                f"Slot {request.slot_id} not found"
            )

        # Confirm reservation (domain logic)
        try:
            slot.confirm()
        except SlotNotReservedException as e:
            raise InvalidInputException(str(e))

        # Persist changes
        saved_slot = self.repository.save(slot)

        # Return DTO
        return SlotMapper.to_response(saved_slot)


class RefuseReservationUseCase:
    """Use case for babysitter refusing a reservation"""

    def __init__(self, repository: AvailabilitySlotRepository):
        self.repository = repository

    def execute(self, request: RefuseSlotRequest) -> SlotResponse:
        # Find slot
        slot = self.repository.find_by_id(request.slot_id)
        if not slot:
            raise SlotNotFoundException(
                f"Slot {request.slot_id} not found"
            )

        # Refuse reservation (domain logic)
        try:
            slot.refuse()
        except SlotNotReservedException as e:
            raise InvalidInputException(str(e))

        # Persist changes
        saved_slot = self.repository.save(slot)

        # Return DTO
        return SlotMapper.to_response(saved_slot)


class ListAvailableSlotsUseCase:
    """Use case for listing available slots"""

    def __init__(self, repository: AvailabilitySlotRepository):
        self.repository = repository

    def execute(
        self, request: ListAvailableSlotsRequest
    ) -> List[SlotResponse]:
        # Parse filters
        week_day = None
        time_slot = None

        if request.week_day:
            week_day = request.week_day

        if request.time_slot:
            time_slot = request.time_slot

        # Query repository
        slots = self.repository.find_available_slots(
            week_day=week_day, time_slot=time_slot
        )

        # Convert to DTOs
        return [SlotMapper.to_response(slot) for slot in slots]
