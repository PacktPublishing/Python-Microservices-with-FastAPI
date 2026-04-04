import uuid
from datetime import UTC, datetime
from pathlib import Path

from tinydb import Query, TinyDB
from tinydb.storages import JSONStorage, MemoryStorage

from shared.domain.entities import Babysitter
from shared.infrastructure.base_repository import BaseRepository


class TinyDBRepository(BaseRepository):
    """TinyDB-based repository implementation.

    Supports both in-memory storage (for testing) and
    file-based storage (for development/lightweight deployments).
    """

    def __init__(
        self,
        db_path: str | None = None,
        in_memory: bool = False,
    ) -> None:
        """Initialize the TinyDB repository.

        Args:
            db_path: Path to the JSON file for persistence.
                     Ignored if in_memory is True.
            in_memory: If True, use in-memory storage
                       (data is lost on restart).
        """
        if in_memory:
            self._db = TinyDB(storage=MemoryStorage)
        else:
            path = db_path or "babysitters_db.json"
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._db = TinyDB(path, storage=JSONStorage)

        self._collection = self._db.table("babysitters")

    async def save_sitter(self, entity: Babysitter) -> Babysitter:
        """Persist an entity. Creates new or updates existing."""
        if entity.id is None:
            entity.id = str(uuid.uuid4())
            entity.created_at = datetime.now(UTC)

        entity.refresh_updated_at()

        q = Query()
        existing = self._collection.search(q.id == entity.id)

        data = entity.model_dump(mode="json")

        if existing:
            self._collection.update(data, q.id == entity.id)
        else:
            self._collection.insert(data)

        return entity

    async def find_sitter_by_id(
        self, id: str
    ) -> Babysitter | None:
        """Find an entity by ID."""
        q = Query()
        results = self._collection.search(q.id == id)
        if results:
            return Babysitter.model_validate(results[0])
        return None

    async def find_all_sitters(
        self,
        filters: dict,
        skip: int,
        limit: int,
    ) -> list[Babysitter]:
        """Find all entities matching filters with pagination."""
        all_docs = self._collection.all()

        filtered = []
        for doc in all_docs:
            if not self._matches_filters(doc, filters):
                continue
            filtered.append(doc)

        # Sort by created_at descending (newest first)
        filtered.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True,
        )

        # Apply pagination
        paginated = filtered[skip : skip + limit]

        return [self._dict_to_entity(d) for d in paginated]

    def _matches_filters(self, doc: dict, filters: dict) -> bool:
        """Check if a document matches all provided filters."""
        if "city" in filters:
            location = doc.get("location", {})
            if location.get("city") != filters["city"]:
                return False

        if "min_rate" in filters:
            if doc.get("hourly_rate", 0) < filters["min_rate"]:
                return False

        if "max_rate" in filters:
            if doc.get("hourly_rate", 0) > filters["max_rate"]:
                return False

        if "language" in filters:
            languages = doc.get("languages", [])
            if filters["language"] not in languages:
                return False

        if "min_experience" in filters:
            exp = doc.get("years_of_experience", 0)
            if exp < filters["min_experience"]:
                return False

        if "is_active" in filters:
            if doc.get("is_active") != filters["is_active"]:
                return False

        return True

    def _dict_to_entity(self, d: dict) -> Babysitter:
        """Convert a TinyDB document dict to a Babysitter entity."""
        return Babysitter.model_validate(d)

    async def delete_sitter(self, entity: Babysitter) -> None:
        """Remove an entity from the repository."""
        if entity.id:
            q = Query()
            self._collection.remove(q.id == entity.id)

    async def find_featured_sitters(
        self, limit: int = 5
    ) -> list[Babysitter]:
        """Find top featured (active, experienced) entities."""
        all_docs = self._collection.all()

        # Filter active only
        active = [d for d in all_docs if d.get("is_active", True)]

        # Sort by years_of_experience descending
        active.sort(
            key=lambda x: x.get("years_of_experience", 0),
            reverse=True,
        )

        # Take top N
        featured = active[:limit]

        return [self._dict_to_entity(d) for d in featured]

    def close(self) -> None:
        """Close the database connection."""
        self._db.close()

    def clear(self) -> None:
        """Clear all data (useful for testing)."""
        self._collection.truncate()
