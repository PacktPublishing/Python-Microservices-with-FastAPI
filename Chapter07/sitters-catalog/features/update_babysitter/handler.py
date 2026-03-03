from fastapi import HTTPException, status

from shared.domain.entities import Babysitter
from shared.infrastructure.base_repository import BaseRepository

from .dto import UpdateBabysitterDTO


async def update_babysitter(
    id: str,
    dto: UpdateBabysitterDTO,
    repo: BaseRepository,
) -> Babysitter:
    """Update a babysitter's information."""
    doc = await repo.find_sitter_by_id(id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Babysitter '{id}' not found",
        )
    for field, value in dto.model_dump(
        exclude_unset=True
    ).items():
        setattr(doc, field, value)
    saved = await repo.save_sitter(doc)
    return saved
