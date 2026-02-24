import asyncio
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from pydantic import BaseModel

from rate_limiter import limiter
from routers.dependencies import (
    get_portal_client,
    get_reservation_client,
)
from services import (
    PortalClientInterface,
    ReservationClientInterface,
    TimeSlot,
    WeekDay,
)

router = APIRouter(prefix="/aggregate", tags=["Aggregation"])


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


async def fetch_aggregated_health(
    portal_client: PortalClientInterface,
    reservation_client: ReservationClientInterface,
) -> HealthStatusResponse:
    """
    Check health of all downstream services in parallel.

    Returns aggregated health status.
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


@router.get("/health", response_model=HealthStatusResponse)
@limiter.limit("30/minute")
async def aggregated_health(
    request: Request,  # Required by slowapi limiter
    portal_client: Annotated[
        PortalClientInterface, Depends(get_portal_client)
    ],
    reservation_client: Annotated[
        ReservationClientInterface,
        Depends(get_reservation_client),
    ],
):
    """
    Aggregated health check across all downstream services.

    Demonstrates parallel health checking of multiple services.
    """
    return await fetch_aggregated_health(
        portal_client,
        reservation_client,
    )


async def fetch_availability_summary(
    reservation_client: ReservationClientInterface,
    week_day: WeekDay | None = None,
    time_slot: TimeSlot | None = None,
) -> AvailabilitySummary:
    """
    Fetch and aggregate slot availability data.

    Returns slots grouped by day and time slot with counts.
    """
    available_slots = (
        await reservation_client.list_available_slots(
            week_day=week_day,
            time_slot=time_slot,
        )
    )

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


@router.get(
    "/availability-summary", response_model=AvailabilitySummary
)
@limiter.limit("30/minute")
async def get_availability_summary(
    request: Request,  # Required by slowapi limiter
    reservation_client: Annotated[
        ReservationClientInterface,
        Depends(get_reservation_client),
    ],
    week_day: Annotated[
        WeekDay | None, Query(description="Filter by day")
    ] = None,
    time_slot: Annotated[
        TimeSlot | None, Query(description="Filter by time slot")
    ] = None,
):
    """
    Aggregated summary of slot availability.

    Returns slots grouped by day and time slot with counts,
    demonstrating data transformation in the gateway.
    """
    try:
        return await fetch_availability_summary(
            reservation_client,
            week_day=week_day,
            time_slot=time_slot,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Reservation service error: {e}",
        )
