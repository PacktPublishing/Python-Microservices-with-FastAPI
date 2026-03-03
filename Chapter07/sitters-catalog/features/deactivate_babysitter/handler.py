from fastapi import HTTPException, status

from shared.domain.entities import Babysitter
from shared.infrastructure.base_repository import BaseRepository


async def deactivate_babysitter(
    id: str,
    repo: BaseRepository,
) -> Babysitter:
    """Soft-delete: set is_active=False, keep the record."""
    doc = await repo.find_sitter_by_id(id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Babysitter '{id}' not found",
        )
    doc.is_active = False
    saved = await repo.save_sitter(doc)
    return saved
