from contextlib import asynccontextmanager
from typing import TypedDict
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from collections.abc import AsyncIterator
from infrastructure.in_memory_slot_repository import (
    InMemorySlotRepository,
)
from domain.repositories import AvailabilitySlotRepository

from .api.routes import router


class State(TypedDict):
    repository: AvailabilitySlotRepository


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:
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
