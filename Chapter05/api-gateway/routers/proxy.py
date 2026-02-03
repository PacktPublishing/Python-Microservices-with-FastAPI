import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse

router = APIRouter()

SERVICE_MAP = {
    "portal": "http://localhost:8002",
    "reservations": "http://localhost:8003",
}


async def proxy_request(
    service_url: str,
    path: str,
    request: Request,
) -> Response:
    async with httpx.AsyncClient() as client:
        url = f"{service_url}{path}"

        # Forward query parameters
        params = dict(request.query_params)

        # Forward headers (excluding host)
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in ("host", "content-length")
        }

        # Get request body if present
        body = await request.body()

        try:
            response = await client.request(
                method=request.method,
                url=url,
                params=params,
                headers=headers,
                content=body if body else None,
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")

        # Determine response class based on content type
        content_type = response.headers.get("content-type", "")

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=content_type,
        )


# Portal proxy routes
@router.get("/portal/home/{lang}", response_class=HTMLResponse, tags=["Portal Proxy"])
async def proxy_portal_home(lang: str, request: Request):
    """Proxy to portal home page with language selection."""
    return await proxy_request(
        SERVICE_MAP["portal"],
        f"/home/{lang}",
        request,
    )


@router.get("/portal/{path:path}", tags=["Portal Proxy"])
async def proxy_portal(path: str, request: Request):
    """Proxy all other portal requests."""
    return await proxy_request(
        SERVICE_MAP["portal"],
        f"/{path}" if path else "/",
        request,
    )


# Reservation proxy routes
@router.get("/reservations/slots", tags=["Reservations Proxy"])
async def proxy_list_slots(request: Request):
    """Proxy to list available slots."""
    return await proxy_request(
        SERVICE_MAP["reservations"],
        "/api/v1/slots",
        request,
    )


@router.post("/reservations/slots", tags=["Reservations Proxy"])
async def proxy_create_slot(request: Request):
    """Proxy to create a new slot."""
    return await proxy_request(
        SERVICE_MAP["reservations"],
        "/api/v1/slots",
        request,
    )


@router.post("/reservations/slots/{slot_id}/reserve", tags=["Reservations Proxy"])
async def proxy_reserve_slot(slot_id: str, request: Request):
    """Proxy to reserve a slot."""
    return await proxy_request(
        SERVICE_MAP["reservations"],
        f"/api/v1/slots/{slot_id}/reserve",
        request,
    )


@router.post("/reservations/slots/{slot_id}/confirm", tags=["Reservations Proxy"])
async def proxy_confirm_reservation(slot_id: str, request: Request):
    """Proxy to confirm a reservation."""
    return await proxy_request(
        SERVICE_MAP["reservations"],
        f"/api/v1/slots/{slot_id}/confirm",
        request,
    )


@router.post("/reservations/slots/{slot_id}/refuse", tags=["Reservations Proxy"])
async def proxy_refuse_reservation(slot_id: str, request: Request):
    """Proxy to refuse a reservation."""
    return await proxy_request(
        SERVICE_MAP["reservations"],
        f"/api/v1/slots/{slot_id}/refuse",
        request,
    )
