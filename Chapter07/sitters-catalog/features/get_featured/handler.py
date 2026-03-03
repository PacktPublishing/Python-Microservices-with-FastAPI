from shared.domain.entities import Babysitter
from shared.infrastructure.base_repository import BaseRepository


async def get_featured_babysitters(
    repo: BaseRepository,
) -> list[Babysitter]:
    """Return the top 5 most experienced active babysitters."""
    docs = await repo.find_featured_sitters(limit=5)
    return docs
