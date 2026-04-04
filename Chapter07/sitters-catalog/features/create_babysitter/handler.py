from shared.domain.entities import Babysitter
from shared.infrastructure.base_repository import BaseRepository

from .dto import CreateBabysitterDTO


async def create_babysitter(
    dto: CreateBabysitterDTO,
    repo: BaseRepository,
) -> Babysitter:
    """Create a new babysitter in the catalog."""
    entity = Babysitter.model_validate(dto.model_dump())
    saved = await repo.save_sitter(entity)
    return saved
