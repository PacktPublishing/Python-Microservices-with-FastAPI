from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from shared.dependencies import get_repository
from shared.dto import BabysitterResponseDTO
from shared.infrastructure.base_repository import BaseRepository

from .dto import BabysitterSearchFilters
from .handler import list_babysitters

router = APIRouter(
    prefix="/api/v1/babysitters", tags=["babysitters"]
)


@router.get("/", response_model=list[BabysitterResponseDTO])
async def list_babysitters_endpoint(
    repo: Annotated[BaseRepository, Depends(get_repository)],
    city: Annotated[
        str | None, Query(description="Filter by city")
    ] = None,
    min_rate: Annotated[
        float | None,
        Query(ge=0, description="Minimum hourly rate"),
    ] = None,
    max_rate: Annotated[
        float | None,
        Query(ge=0, description="Maximum hourly rate"),
    ] = None,
    language: Annotated[
        str | None, Query(description="Filter by spoken language")
    ] = None,
    min_experience: Annotated[
        int | None,
        Query(ge=0, description="Minimum years of experience"),
    ] = None,
    is_active: Annotated[
        bool | None, Query(description="Filter by active status")
    ] = True,
    skip: Annotated[
        int, Query(ge=0, description="Pagination offset")
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Page size (max 100)"),
    ] = 20,
) -> Any:
    """Search and list babysitters with optional filters."""
    filters = BabysitterSearchFilters(
        city=city,
        min_rate=min_rate,
        max_rate=max_rate,
        language=language,
        min_experience=min_experience,
        is_active=is_active,
    )
    return await list_babysitters(filters, skip, limit, repo)
