from typing import Annotated, Any

from fastapi import APIRouter, Depends

from shared.dependencies import get_repository
from shared.dto import BabysitterResponseDTO
from shared.infrastructure import BaseRepository

from .handler import get_featured_babysitters

router = APIRouter(
    prefix="/api/v1/babysitters", tags=["babysitters"]
)


@router.get("/featured", response_model=list[BabysitterResponseDTO])
async def get_featured_endpoint(
    repo: Annotated[BaseRepository, Depends(get_repository)],
) -> Any:
    """Return the top 5 most experienced active babysitters."""
    return await get_featured_babysitters(repo)
