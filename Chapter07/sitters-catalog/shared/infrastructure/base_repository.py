from abc import ABC, abstractmethod

from shared.domain.entities import Babysitter


class BaseRepository(ABC):
    @abstractmethod
    async def save_sitter(self, sitter: Babysitter) -> Babysitter:
        """Persist an entity and return it with any
        generated fields (e.g., ID).
        """

    @abstractmethod
    async def find_sitter_by_id(
        self, id: str
    ) -> Babysitter | None:
        """Find an entity by its unique identifier."""

    @abstractmethod
    async def find_all_sitters(
        self,
        filters: dict,
        skip: int,
        limit: int,
    ) -> list[Babysitter]:
        """Find all entities matching the given filters
        with pagination support.
        """

    @abstractmethod
    async def delete_sitter(self, entity: Babysitter) -> None:
        """Remove an entity from the repository."""

    @abstractmethod
    async def find_featured_sitters(
        self, limit: int = 5
    ) -> list[Babysitter]:
        """Find featured (top experienced, active) entities."""
