from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI

from container import Container
from middleware import RateLimiter, RateLimitMiddleware
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
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
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
    title="Babysitting API Gateway",
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

# Configure rate limiter with tiered limits
rate_limiter = RateLimiter()

# Public tier - portal endpoints (highest limit)
rate_limiter.add_rule(
    path_matcher=lambda p: p.startswith("/portal"),
    requests_per_minute=100,
    burst_size=120,
)

# Aggregation tier - composite endpoints
rate_limiter.add_rule(
    path_matcher=lambda p: p.startswith("/aggregate"),
    requests_per_minute=30,
    burst_size=40,
)

# Read tier - GET operations on reservations
rate_limiter.add_rule(
    path_matcher=lambda p: p.startswith("/reservations")
    and "/slots" in p,
    requests_per_minute=60,
    burst_size=80,
)

rate_limiter.add_rule(
    path_matcher=lambda p: "/reserve" in p,
    requests_per_minute=20,
    burst_size=25,
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware, # ty: ignore[invalid-argument-type]
    # ty bug see https://github.com/astral-sh/ty/issues/1635
    rate_limiter=rate_limiter,
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
