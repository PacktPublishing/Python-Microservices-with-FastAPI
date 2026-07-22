import logging
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI, Request, Response

from domain.repositories import AvailabilitySlotRepository
from infrastructure.in_memory_slot_repository import (
    InMemorySlotRepository,
)

from .api.routes import router
from .middleware import StateCheckMiddleware

logger = logging.getLogger("uvicorn")


class State(TypedDict):
    repository: AvailabilitySlotRepository


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[State]:
    """
    Lifespan context manager for application startup and shutdown.
    Initializes the repository and stores it in application state.
    """
    repository = InMemorySlotRepository()

    yield {"repository": repository}


app = FastAPI(
    title="Babysitter Reservation API",
    lifespan=lifespan,
)


@app.get(
    "/health",
    summary="Health check",
    description="Check if the API is running",
    tags=["Health"],
)
def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "babysitter-reservation-api",
    }


app.include_router(router=router)


@app.middleware("http")
async def measuring_request_performance(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
):
    start_time = time.perf_counter()
    logger.debug("measuring performance logger")
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    logger.debug(f"measured performance:{str(process_time)}")
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.add_middleware(StateCheckMiddleware) # ty: ignore[invalid-argument-type] known issue with ty
