from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI

from config import RepositoryType, settings
from features.create_babysitter.route import (
    router as create_router,
)
from features.deactivate_babysitter.route import (
    router as deactivate_router,
)
from features.delete_babysitter.route import (
    router as delete_router,
)
from features.get_babysitter.route import (
    router as get_router,
)
from features.get_featured.route import (
    router as featured_router,
)
from features.health.route import router as health_router
from features.list_babysitters.route import (
    router as list_router,
)
from features.update_babysitter.route import (
    router as update_router,
)
from shared.infrastructure import (
    BaseRepository,
    MongoDBRepository,
    TinyDBRepository,
)


class State(TypedDict):
    repository: BaseRepository


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[State]:
    if settings.repository_type == RepositoryType.MONGO:
        yield {
            "repository": MongoDBRepository(settings.mongo_uri)
        }
    elif settings.repository_type == RepositoryType.TINYDB_MEMORY:
        yield {"repository": TinyDBRepository(in_memory=False)}
    elif settings.repository_type == RepositoryType.TINYDB_FILE:
        yield {
            "repository": TinyDBRepository(
                db_path=settings.tinydb_path
            )
        }


app = FastAPI(
    title=settings.app_title,
    debug=settings.debug,
    lifespan=lifespan,
)

# Register feature routes
# Note: featured_router must come before get_router to avoid
# /featured being shadowed by /{id}
app.include_router(health_router)
app.include_router(create_router)
app.include_router(featured_router)
app.include_router(list_router)
app.include_router(get_router)
app.include_router(update_router)
app.include_router(delete_router)
app.include_router(deactivate_router)
