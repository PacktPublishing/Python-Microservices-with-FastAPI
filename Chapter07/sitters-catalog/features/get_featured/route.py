from typing import Annotated

from fastapi import APIRouter, Depends

from shared.dependencies import get_repository
from shared.dto import BabysitterResponseDTO

from .handler import get_featured_babysitters

router = APIRouter(
    prefix="/api/v1/babysitters", tags=["babysitters"]
)


@router.get("/featured")
async def get_featured_endpoint(
    repo: Annotated[object, Depends(get_repository)],
) -> list[BabysitterResponseDTO]:
    """Return the top 5 most experienced active babysitters."""
    return await get_featured_babysitters(repo)
