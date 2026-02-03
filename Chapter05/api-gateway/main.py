from fastapi import FastAPI

from middleware import RateLimiter, RateLimitMiddleware
from routers import aggregation_router, proxy_router

app = FastAPI(
    title="Babysitting API Gateway",
    description="""
API Gateway demonstrating aggregation patterns and rate limiting.

## Features

### Proxy Routes
Pass-through routes that forward requests to downstream services:
- `/portal/*` - Portal service (language-aware home pages)
- `/reservations/*` - Reservation service (slot management)

### Aggregation Routes
Composite endpoints that combine data from multiple services:
- `/aggregate/dashboard` - Combined welcome message and availability
- `/aggregate/availability-summary` - Slot statistics and groupings
- `/aggregate/quick-reserve` - Orchestrated slot creation and reservation
- `/aggregate/health` - Aggregated health status of all services

### Rate Limiting
Tiered rate limits applied by endpoint type:
- Public endpoints (portal): 100 req/min
- Read operations (GET): 60 req/min
- Write operations (POST): 20 req/min
- Aggregated endpoints: 30 req/min
    """,
    version="1.0.0",
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
    path_matcher=lambda p: p.startswith("/reservations") and "/slots" in p,
    requests_per_minute=60,
    burst_size=80,
)

# Write tier - POST operations (lowest limit for mutations)
rate_limiter.add_rule(
    path_matcher=lambda p: "/reserve" in p or "/confirm" in p or "/refuse" in p,
    requests_per_minute=20,
    burst_size=25,
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# Include routers
app.include_router(proxy_router)
app.include_router(aggregation_router)


@app.get("/", tags=["Gateway"])
async def root():
    return {
        "message": "Babysitting API Gateway",
        "docs": "/docs",
        "services": {
            "portal": "http://localhost:8002",
            "reservations": "http://localhost:8003",
        },
        "endpoints": {
            "proxy": ["/portal/*", "/reservations/*"],
            "aggregation": [
                "/aggregate/dashboard",
                "/aggregate/availability-summary",
                "/aggregate/quick-reserve",
                "/aggregate/health",
            ],
        },
    }


@app.get("/health", tags=["Gateway"])
async def health():
    return {"status": "healthy", "service": "api-gateway"}
