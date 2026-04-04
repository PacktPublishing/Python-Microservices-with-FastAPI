from typing import Annotated

from fastapi import APIRouter, Depends, Path

from shared.dependencies import get_repository
from shared.dto import BabysitterResponseDTO

from .handler import deactivate_babysitter

router = APIRouter(
    prefix="/api/v1/babysitters", tags=["babysitters"]
)

BabysitterIdDep = Annotated[
    str,
    Path(description="Babysitter ID"),
]


@router.post("/{id}/deactivate")
async def deactivate_babysitter_endpoint(
    id: BabysitterIdDep,
    repo: Annotated[object, Depends(get_repository)],
) -> BabysitterResponseDTO:
    """Soft-delete: set is_active=False, keep the record."""
    return await deactivate_babysitter(id, repo)
