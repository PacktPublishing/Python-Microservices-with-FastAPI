from typing import Annotated

from fastapi import APIRouter, Depends, Path

from shared.dependencies import get_repository
from shared.dto import BabysitterResponseDTO
from shared.infrastructure.base_repository import BaseRepository

from .dto import UpdateBabysitterDTO
from .handler import update_babysitter

router = APIRouter(
    prefix="/api/v1/babysitters", tags=["babysitters"]
)

BabysitterIdDep = Annotated[
    str,
    Path(description="Babysitter ID"),
]


@router.put("/{id}")
async def update_babysitter_endpoint(
    id: BabysitterIdDep,
    dto: UpdateBabysitterDTO,
    repo: Annotated[BaseRepository, Depends(get_repository)],
) -> BabysitterResponseDTO:
    """Full update — replace all provided fields."""
    return await update_babysitter(id, dto, repo)


@router.patch("/{id}")
async def partial_update_babysitter_endpoint(
    id: BabysitterIdDep,
    dto: UpdateBabysitterDTO,
    repo: Annotated[BaseRepository, Depends(get_repository)],
) -> BabysitterResponseDTO:
    """Partial update — only sent fields are changed."""
    return await update_babysitter(id, dto, repo)
