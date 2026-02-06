import asyncio
from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from pydantic import BaseModel

from services import (
    PortalClientInterface,
    ReservationClientInterface,
)

router = APIRouter(prefix="/aggregate", tags=["Aggregation"])

Lang = Literal["en", "fr", "it", "pt"]
WeekDay = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]
TimeSlot = Literal["morning", "afternoon", "night"]


class DashboardResponse(BaseModel):
    welcome_content: str
    available_slots: list[dict]
    total_available: int


class AvailabilitySummary(BaseModel):
    total_slots: int
    by_day: dict[str, int]
    by_time: dict[str, int]
    slots: list[dict]


class HealthStatusResponse(BaseModel):
    gateway: str
    portal_service: bool
    reservation_service: bool
    all_healthy: bool


def get_portal_client(request: Request) -> PortalClientInterface:
    return request.state.portal_client


def get_reservation_client(
    request: Request,
) -> ReservationClientInterface:
    return request.state.reservation_client


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    lang: Lang = Query(
        default="en", description="Language for welcome message"
    ),
    name: str = Query(
        default="", description="Name for personalized greeting"
    ),
    portal_client: PortalClientInterface = Depends(
        get_portal_client
    ),
    reservation_client: ReservationClientInterface = Depends(
        get_reservation_client
    ),
):
    """
    Aggregated dashboard combining portal welcome and available slots.

    This endpoint demonstrates API aggregation by calling multiple
    downstream services in parallel and combining their responses.
    """
    # Call both services in parallel
    welcome_task = portal_client.get_home(lang=lang, name=name)
    slots_task = reservation_client.list_slots()

    try:
        welcome_content, slots = await asyncio.gather(
            welcome_task,
            slots_task,
            return_exceptions=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Service error: {e}"
        )

    # Handle individual service failures gracefully
    if isinstance(welcome_content, Exception):
        welcome_content = (
            "<p>Welcome service temporarily unavailable</p>"
        )
    if isinstance(slots, Exception):
        slots = []

    # Filter to only available slots
    available_slots = [
        s for s in slots if s.get("status") == "available"
    ]

    return DashboardResponse(
        welcome_content=welcome_content,
        available_slots=available_slots,
        total_available=len(available_slots),
    )


@router.get(
    "/availability-summary", response_model=AvailabilitySummary
)
async def get_availability_summary(
    week_day: WeekDay | None = Query(
        default=None, description="Filter by day"
    ),
    time_slot: TimeSlot | None = Query(
        default=None, description="Filter by time slot"
    ),
    reservation_client: ReservationClientInterface = Depends(
        get_reservation_client
    ),
):
    """
    Aggregated summary of slot availability.

    Returns slots grouped by day and time slot with counts,
    demonstrating data transformation in the gateway.
    """
    try:
        slots = await reservation_client.list_slots(
            week_day=week_day,
            time_slot=time_slot,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Reservation service error: {e}",
        )

    # Only count available slots
    available_slots = [
        s for s in slots if s.get("status") == "available"
    ]

    # Aggregate by day
    by_day: dict[str, int] = {}
    for slot in available_slots:
        day = slot.get("week_day", "unknown")
        by_day[day] = by_day.get(day, 0) + 1

    # Aggregate by time slot
    by_time: dict[str, int] = {}
    for slot in available_slots:
        time = slot.get("time_slot", "unknown")
        by_time[time] = by_time.get(time, 0) + 1

    return AvailabilitySummary(
        total_slots=len(available_slots),
        by_day=by_day,
        by_time=by_time,
        slots=available_slots,
    )


@router.get("/health", response_model=HealthStatusResponse)
async def aggregated_health(
    portal_client: PortalClientInterface = Depends(
        get_portal_client
    ),
    reservation_client: ReservationClientInterface = Depends(
        get_reservation_client
    ),
):
    """
    Aggregated health check across all downstream services.

    Demonstrates parallel health checking of multiple services.
    """
    portal_health, reservation_health = await asyncio.gather(
        portal_client.health_check(),
        reservation_client.health_check(),
    )

    return HealthStatusResponse(
        gateway="healthy",
        portal_service=portal_health,
        reservation_service=reservation_health,
        all_healthy=portal_health and reservation_health,
    )
