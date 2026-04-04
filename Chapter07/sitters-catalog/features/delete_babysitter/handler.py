from fastapi import HTTPException, status

from shared.infrastructure.base_repository import BaseRepository


async def delete_babysitter(
    id: str,
    repo: BaseRepository,
) -> None:
    """Permanently remove a babysitter from the catalog."""
    doc = await repo.find_sitter_by_id(id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Babysitter '{id}' not found",
        )
    await repo.delete_sitter(doc)
