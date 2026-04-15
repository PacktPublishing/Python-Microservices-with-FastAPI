from shared.domain.entities import Babysitter
from shared.infrastructure.base_repository import BaseRepository

from .dto import BabysitterSearchFilters


async def list_babysitters(
    filters: BabysitterSearchFilters,
    skip: int,
    limit: int,
    repo: BaseRepository,
) -> list[Babysitter]:
    """Search and list babysitters with optional filters."""
    raw: dict = {}
    if filters.city is not None:
        raw["city"] = filters.city
    if filters.min_rate is not None:
        raw["min_rate"] = filters.min_rate
    if filters.max_rate is not None:
        raw["max_rate"] = filters.max_rate
    if filters.language is not None:
        raw["language"] = filters.language
    if filters.min_experience is not None:
        raw["min_experience"] = filters.min_experience
    if filters.is_active is not None:
        raw["is_active"] = filters.is_active
    docs = await repo.find_all_sitters(raw, skip, limit)
    return docs
