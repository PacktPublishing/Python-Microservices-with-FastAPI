from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI, Request, status
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIASGIMiddleware

from container import Container
from rate_limiter import limiter
from routers import aggregation_router, proxy_router
from services import (
    PortalClientInterface,
    ReservationClientInterface,
)

SERVICE_URLS = {
    "portal": "",
    "reservations": "http://localhost:8003",
}


class State(TypedDict):
    portal_client: PortalClientInterface
    reservation_client: ReservationClientInterface


container = Container()
container.config.from_yaml("config.yaml")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[State]:
    # Startup: Initialize service clients from container
    portal_client = container.portal_client()
    reservation_client = container.reservation_client()

    yield {
        "portal_client": portal_client,
        "reservation_client": reservation_client,
    }

    # Shutdown: Cleanup if needed
    pass


app = FastAPI(
    title="Parents API Gateway",
    description="""
API Gateway demonstrating aggregation patterns and rate limiting.

## Features

### Portal Routes
- `/portal/home/{lang}` - Get language-aware home page

### Reservation Routes
- `/reservations/slots` - Get all reservations with optional filtering
- `/reservations/slots/{slot_id}/reserve` - Reserve a slot

### Aggregation Routes
Composite endpoints that combine data from multiple services:
- `/aggregate/availability-summary` - Slot statistics and groupings
- `/aggregate/health` - Aggregated health status of all services

### Rate Limiting
Tiered rate limits applied by endpoint type:
- Public endpoints (portal): 100 req/min
- Read operations (GET): 60 req/min
- Write operations (POST): 20 req/min
- Aggregated endpoints: 30 req/min
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Attach limiter to app state for slowapi
app.state.limiter = limiter


# Custom rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    _request: Request, exc: RateLimitExceeded
):
    from fastapi.responses import JSONResponse

    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded",
            "retry_after": str(retry_after),
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(exc.detail),
        },
    )


# Add SlowAPI ASGI middleware
app.add_middleware(
    SlowAPIASGIMiddleware  # ty: ignore[invalid-argument-type]
    # due to ty: see updates at https://github.com/astral-sh/ty/issues/1635
)

# Include routers
app.include_router(proxy_router)
app.include_router(aggregation_router)


@app.get("/", tags=["Gateway"])
async def root():
    return {
        "message": "Babysitting API Gateway",
        "docs": "/docs",
        "services": SERVICE_URLS,
        "endpoints": {
            "portal": ["/portal/home/{lang}"],
            "reservations": [
                "/reservations/slots",
                "/reservations/slots/{slot_id}/reserve",
            ],
            "aggregation": [
                "/aggregate/availability-summary",
                "/aggregate/health",
            ],
        },
    }


@app.get("/health", tags=["Gateway"])
async def health():
    return {"status": "healthy", "service": "api-gateway"}
