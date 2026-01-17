from fastapi import APIRouter, HTTPException, Request, status

from application.dtos import CreateSlotRequest
from application.exceptions import InvalidInputException
from application.use_cases import CreateAvailabilitySlotUseCase
from domain.value_objects import TimeSlot, WeekDay

from .schemas import CreateSlotRequestSchema, SlotResponseSchema

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
