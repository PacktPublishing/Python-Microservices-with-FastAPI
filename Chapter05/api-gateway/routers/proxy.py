from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Query,
    Request,
)
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr

from rate_limiter import limiter
from routers.dependencies import (
    get_portal_client,
    get_reservation_client,
)
from services import (
    Lang,
    PortalClientInterface,
    ReservationClientInterface,
    TimeSlot,
    WeekDay,
)

router = APIRouter()


class ReservationRequest(BaseModel):
    parent_email: EmailStr
    description: str = ""


async def fetch_portal_home(
    client: PortalClientInterface,
    lang: Lang = "en",
    name: str = "",
) -> str:
    """Fetch the portal home page for a given language."""
    return await client.get_home(lang=lang, name=name)


async def get_all_available_slots(
    client: ReservationClientInterface,
    week_day: WeekDay | None = None,
    time_slot: TimeSlot | None = None,
) -> list[dict]:
    """Fetch all reservations with optional filtering."""
    return await client.list_available_slots(
        week_day=week_day, time_slot=time_slot
    )


async def make_reservation(
    client: ReservationClientInterface,
    slot_id: UUID,
    parent_email: str,
    description: str = "",
) -> dict:
    """Make a reservation for a slot."""
    return await client.reserve_slot(
        slot_id=slot_id,
        parent_email=parent_email,
        description=description,
    )


@router.get(
    "/portal/home/{lang}",
    response_class=HTMLResponse,
    tags=["Portal"],
)
@limiter.limit("100/minute")
async def get_portal_home_page(
    request: Request,  # Required by slowapi limiter
    lang: Lang,
    client: Annotated[
        PortalClientInterface, Depends(get_portal_client)
    ],
    name: Annotated[str, Body()] = "",
) -> str:
    """Get the portal home page with language selection."""
    try:
        return await fetch_portal_home(
            client, lang=lang, name=name
        )
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Portal service error: {e}"
        )


@router.get("/reservations/slots", tags=["Reservations"])
@limiter.limit("60/minute")
async def get_all_reservations(
    request: Request,  # Required by slowapi limiter
    client: Annotated[
        ReservationClientInterface,
        Depends(get_reservation_client),
    ],
    week_day: Annotated[WeekDay | None, Query()] = None,
    time_slot: Annotated[TimeSlot | None, Query()] = None,
) -> list[dict]:
    """Get all reservations with optional filtering."""
    try:
        return await get_all_available_slots(
            client, week_day=week_day, time_slot=time_slot
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Reservation service error: {e}",
        )


@router.post(
    "/reservations/slots/{slot_id}/reserve", tags=["Reservations"]
)
@limiter.limit("20/minute")
async def reserve_slot(
    request: Request,  # Required by slowapi limiter
    slot_id: UUID,
    reservation: ReservationRequest,
    client: Annotated[
        ReservationClientInterface,
        Depends(get_reservation_client),
    ],
) -> dict:
    """Reserve a slot."""
    try:
        return await make_reservation(
            client,
            slot_id=slot_id,
            parent_email=reservation.parent_email,
            description=reservation.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Reservation service error: {e}",
        )
