from typing import Annotated, Any

from fastapi import APIRouter, Depends, status

from shared.dependencies import (
    get_repository,
)
from shared.dto import BabysitterResponseDTO
from shared.infrastructure import BaseRepository

from .dto import CreateBabysitterDTO
from .handler import create_babysitter

router = APIRouter(
    prefix="/api/v1/babysitters", tags=["babysitters"]
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BabysitterResponseDTO)
async def create_babysitter_endpoint(
    dto: CreateBabysitterDTO,
    repo: Annotated[BaseRepository, Depends(get_repository)],
) -> Any:
    """Register a new babysitter in the catalog."""
    babysitter = await create_babysitter(dto, repo)
    return babysitter
