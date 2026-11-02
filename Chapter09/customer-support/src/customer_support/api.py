from typing import Annotated

from fastapi import Depends, FastAPI

from .config import Settings
from .knowledge import KnowledgeBase, SyncReport
from .response_models import HealthResponse

app = FastAPI(title="Customer Support")


def get_knowledge_base() -> KnowledgeBase:
    """Open the knowledge base configured by the environment."""
    return KnowledgeBase(Settings().knowledge)


@app.get("/health")
def health() -> HealthResponse:
    """Report that the service is up."""
    return HealthResponse(status="ok")


@app.post("/knowledge/sync")
def sync_knowledge(
    knowledge_base: Annotated[
        KnowledgeBase, Depends(get_knowledge_base)
    ],
) -> SyncReport:
    """Sync the source folder into the knowledge base."""
    return knowledge_base.sync()
