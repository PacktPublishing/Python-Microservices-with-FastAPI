from typing import Annotated

from fastapi import APIRouter, Depends, Path

from shared.dependencies import get_repository
from shared.dto import BabysitterResponseDTO

from .handler import get_babysitter_by_id

router = APIRouter(
    prefix="/api/v1/babysitters", tags=["babysitters"]
)

BabysitterIdDep = Annotated[
    str,
    Path(description="Babysitter ID"),
]


@router.get("/{id}")
async def get_babysitter_endpoint(
    id: BabysitterIdDep,
    repo: Annotated[object, Depends(get_repository)],
) -> BabysitterResponseDTO:
    """Fetch a single babysitter by ID."""
    return await get_babysitter_by_id(id, repo)
