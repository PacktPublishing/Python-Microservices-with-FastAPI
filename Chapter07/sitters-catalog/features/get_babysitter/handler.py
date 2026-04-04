from fastapi import HTTPException, status

from shared.domain.entities import Babysitter
from shared.infrastructure.base_repository import BaseRepository


async def get_babysitter_by_id(
    id: str,
    repo: BaseRepository,
) -> Babysitter:
    """Fetch a single babysitter by ID."""
    doc = await repo.find_sitter_by_id(id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Babysitter '{id}' not found",
        )
    return doc
