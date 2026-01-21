from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    status,
)

from application.dtos import (
    ConfirmSlotRequest,
    CreateSlotRequest,
    ListAvailableSlotsRequest,
    RefuseSlotRequest,
    ReserveSlotRequest,
)
from application.exceptions import (
    InvalidInputException,
    SlotNotFoundException,
)
from application.use_cases import (
    ConfirmReservationUseCase,
    CreateAvailabilitySlotUseCase,
    ListAvailableSlotsUseCase,
    RefuseReservationUseCase,
    ReserveSlotUseCase,
)
from domain.value_objects import TimeSlot, WeekDay

from .schemas import (
    CreateSlotRequestSchema,
    ReserveSlotRequestSchema,
    SlotResponseSchema,
    TimeSlotSchema,
    WeekDaySchema,
)

router = APIRouter(prefix="/api/v1")


@router.post(
    "/slots",
    response_model_exclude_none=False,
    status_code=status.HTTP_201_CREATED,
    summary="Create availability slot",
    description="Create a new babysitter availability slot for a specific day and time",
    responses={
        201: {"description": "Slot created successfully"},
    },
)
async def create_availability_slot(
    request: Request, create_request: CreateSlotRequestSchema
) -> SlotResponseSchema:
    repository = request.state.repository

    try:
        dto_request = CreateSlotRequest(
            week_day=WeekDay(create_request.week_day),
            time_slot=TimeSlot(create_request.time_slot),
            babysitter_name=create_request.babysitter_name,
        )

        use_case = CreateAvailabilitySlotUseCase(repository)

        result = use_case.execute(dto_request)

        return SlotResponseSchema(
            id=result.id,
            week_day=result.week_day.value,
            time_slot=result.time_slot.value,
            babysitter_name=result.babysitter_name,
            status=result.status,
            reservation_email=result.reservation_email,
            reservation_description=result.reservation_description,
            reserved_at=result.reserved_at,
            confirmed_at=result.confirmed_at,
        )
    except InvalidInputException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get(
    "/slots",
    response_model_exclude_none=False,
    summary="List available slots",
    description="Get a list of available babysitter slots with optional filters",
)
async def list_available_slots(
    request: Request,
    week_day: WeekDaySchema | None = Query(
        None, description="Filter by day of the week"
    ),
    time_slot: TimeSlotSchema | None = Query(
        None, description="Filter by time slot"
    ),
) -> list[SlotResponseSchema]:
    repository = request.state.repository

    dto_request = ListAvailableSlotsRequest(
        week_day=WeekDay(week_day.value) if week_day else None,
        time_slot=TimeSlot(time_slot.value)
        if time_slot
        else None,
    )

    use_case = ListAvailableSlotsUseCase(repository)
    results = use_case.execute(dto_request)

    return [
        SlotResponseSchema(
            id=result.id,
            week_day=result.week_day.value,
            time_slot=result.time_slot.value,
            babysitter_name=result.babysitter_name,
            status=result.status,
            reservation_email=result.reservation_email,
            reservation_description=result.reservation_description,
            reserved_at=result.reserved_at,
            confirmed_at=result.confirmed_at,
        )
        for result in results
    ]


@router.post(
    "/slots/{slot_id}/reserve",
    response_model_exclude_none=False,
    summary="Reserve a slot",
    description="Reserve an available babysitter slot",
    responses={
        200: {"description": "Slot reserved successfully"},
        404: {"description": "Slot not found"},
        400: {
            "description": "Slot not available or invalid input"
        },
    },
)
async def reserve_slot(
    request: Request,
    slot_id: UUID,
    reserve_request: ReserveSlotRequestSchema,
) -> SlotResponseSchema:
    repository = request.state.repository

    try:
        dto_request = ReserveSlotRequest(
            slot_id=slot_id,
            parent_email=reserve_request.parent_email,
            description=reserve_request.description,
        )

        use_case = ReserveSlotUseCase(repository)
        result = use_case.execute(dto_request)

        return SlotResponseSchema(
            id=result.id,
            week_day=result.week_day.value,
            time_slot=result.time_slot.value,
            babysitter_name=result.babysitter_name,
            status=result.status,
            reservation_email=result.reservation_email,
            reservation_description=result.reservation_description,
            reserved_at=result.reserved_at,
            confirmed_at=result.confirmed_at,
        )
    except SlotNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except InvalidInputException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post(
    "/slots/{slot_id}/confirm",
    response_model_exclude_none=False,
    summary="Confirm a reservation",
    description="Babysitter confirms a pending reservation",
    responses={
        200: {
            "description": "Reservation confirmed successfully"
        },
        404: {"description": "Slot not found"},
        400: {
            "description": "Slot not reserved or invalid state"
        },
    },
)
async def confirm_reservation(
    request: Request,
    slot_id: UUID,
) -> SlotResponseSchema:
    repository = request.state.repository

    try:
        dto_request = ConfirmSlotRequest(slot_id=slot_id)

        use_case = ConfirmReservationUseCase(repository)
        result = use_case.execute(dto_request)

        return SlotResponseSchema(
            id=result.id,
            week_day=result.week_day.value,
            time_slot=result.time_slot.value,
            babysitter_name=result.babysitter_name,
            status=result.status,
            reservation_email=result.reservation_email,
            reservation_description=result.reservation_description,
            reserved_at=result.reserved_at,
            confirmed_at=result.confirmed_at,
        )
    except SlotNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except InvalidInputException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post(
    "/slots/{slot_id}/refuse",
    response_model_exclude_none=False,
    summary="Refuse a reservation",
    description="Babysitter refuses a pending reservation",
    responses={
        200: {"description": "Reservation refused successfully"},
        404: {"description": "Slot not found"},
        400: {
            "description": "Slot not reserved or invalid state"
        },
    },
)
async def refuse_reservation(
    request: Request,
    slot_id: UUID,
) -> SlotResponseSchema:
    repository = request.state.repository

    try:
        dto_request = RefuseSlotRequest(slot_id=slot_id)

        use_case = RefuseReservationUseCase(repository)
        result = use_case.execute(dto_request)

        return SlotResponseSchema(
            id=result.id,
            week_day=result.week_day.value,
            time_slot=result.time_slot.value,
            babysitter_name=result.babysitter_name,
            status=result.status,
            reservation_email=result.reservation_email,
            reservation_description=result.reservation_description,
            reserved_at=result.reserved_at,
            confirmed_at=result.confirmed_at,
        )
    except SlotNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except InvalidInputException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
