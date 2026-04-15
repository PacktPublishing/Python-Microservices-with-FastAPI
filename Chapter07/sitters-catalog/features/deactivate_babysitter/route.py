from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path

from shared.dependencies import get_repository
from shared.dto import BabysitterResponseDTO
from shared.infrastructure import BaseRepository

from .handler import deactivate_babysitter

router = APIRouter(
    prefix="/api/v1/babysitters", tags=["babysitters"]
)

BabysitterIdDep = Annotated[
    str,
    Path(description="Babysitter ID"),
]


@router.post("/{id}/deactivate", response_model=BabysitterResponseDTO)
async def deactivate_babysitter_endpoint(
    id: BabysitterIdDep,
    repo: Annotated[BaseRepository, Depends(get_repository)],
) -> Any:
    """Soft-delete: set is_active=False, keep the record."""
    return await deactivate_babysitter(id, repo)
