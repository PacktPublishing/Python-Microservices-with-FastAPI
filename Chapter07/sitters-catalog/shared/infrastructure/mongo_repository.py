from datetime import UTC, datetime

from bson import ObjectId
from pymongo import AsyncMongoClient

from shared.domain.entities import Babysitter
from shared.infrastructure.base_repository import BaseRepository


class MongoDBRepository(BaseRepository):
    """MongoDB repository using PyMongo async."""

    def __init__(self, mongo_url: str) -> None:
        self.client = AsyncMongoClient(mongo_url)
        db = self.client.sitter_calatog_app
        self._collection = db.babysitters

    async def save_sitter(self, entity: Babysitter) -> Babysitter:
        """Persist an entity. Creates new or updates existing."""
        entity.refresh_updated_at()
        data = entity.model_dump(exclude={"id"})

        if entity.id:
            # Update existing document
            await self._collection.replace_one(
                {"_id": ObjectId(entity.id)},
                data,
            )
        else:
            # Insert new document
            entity.created_at = datetime.now(UTC)
            data["created_at"] = entity.created_at
            result = await self._collection.insert_one(data)
            entity.id = str(result.inserted_id)

        return entity

    async def find_sitter_by_id(
        self, id: str
    ) -> Babysitter | None:
        """Find an entity by its unique identifier."""
        try:
            doc = await self._collection.find_one(
                {"_id": ObjectId(id)}
            )
            if doc:
                return self._to_entity(doc)
        except Exception:
            pass
        return None

    async def find_all_sitters(
        self,
        filters: dict,
        skip: int,
        limit: int,
    ) -> list[Babysitter]:
        """Find all entities matching filters with pagination."""
        query = self._build_query(filters)
        cursor = (
            self._collection.find(query).skip(skip).limit(limit)
        )
        return [
            Babysitter.model_validate(doc) async for doc in cursor
        ]

    async def delete_sitter(self, entity: Babysitter) -> None:
        """Remove an entity from the repository."""
        if entity.id:
            await self._collection.delete_one(
                {"_id": ObjectId(entity.id)}
            )

    async def find_featured_sitters(
        self, limit: int = 5
    ) -> list[Babysitter]:
        """Find top featured (active, experienced) entities."""
        cursor = (
            self._collection.find({"is_active": True})
            .sort("years_of_experience", -1)
            .limit(limit)
        )
        return [self._to_entity(doc) async for doc in cursor]

    def _build_query(self, filters: dict) -> dict:
        """Build MongoDB query from filter parameters."""
        query: dict = {}

        if "city" in filters:
            query["location.city"] = filters["city"]

        if "min_rate" in filters:
            query.setdefault("hourly_rate", {})["$gte"] = filters[
                "min_rate"
            ]

        if "max_rate" in filters:
            query.setdefault("hourly_rate", {})["$lte"] = filters[
                "max_rate"
            ]

        if "language" in filters:
            query["languages"] = filters["language"]

        if "min_experience" in filters:
            query["years_of_experience"] = {
                "$gte": filters["min_experience"]
            }

        if "is_active" in filters:
            query["is_active"] = filters["is_active"]

        return query
