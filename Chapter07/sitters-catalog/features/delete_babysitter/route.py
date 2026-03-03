from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from shared.dependencies import get_repository

from .handler import delete_babysitter

router = APIRouter(
    prefix="/api/v1/babysitters", tags=["babysitters"]
)

BabysitterIdDep = Annotated[
    str,
    Path(description="Babysitter ID"),
]


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_babysitter_endpoint(
    id: BabysitterIdDep,
    repo: Annotated[object, Depends(get_repository)],
) -> None:
    """Permanently remove. Use /deactivate for soft-delete."""
    await delete_babysitter(id, repo)
