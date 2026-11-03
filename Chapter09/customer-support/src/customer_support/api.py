from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
)
from fastapi.responses import StreamingResponse

from .agent import build_agent
from .chat import SupportChat
from .config import Settings
from .conversations import (
    Conversation,
    ConversationConflict,
    ConversationNotFound,
    ConversationRepository,
    Database,
)
from .knowledge import KnowledgeBase, SyncReport
from .response_models import HealthResponse, QuestionRequest


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open the database and wire the chat service for the app's life."""
    settings = Settings()
    database = Database(settings.database)
    await database.initialize()
    app.state.chat = SupportChat(
        build_agent(settings.llm),
        KnowledgeBase(settings.knowledge),
        ConversationRepository(database.sessions),
        settings.llm,
    )
    yield
    await database.close()


app = FastAPI(title="Customer Support", lifespan=lifespan)


def get_knowledge_base() -> KnowledgeBase:
    """Open the knowledge base configured by the environment."""
    return KnowledgeBase(Settings().knowledge)


def get_chat(request: Request) -> SupportChat:
    """Read the chat service created by the lifespan."""
    chat: SupportChat = request.app.state.chat
    return chat


def get_user_id(
    x_user_id: Annotated[str, Header(min_length=1)],
) -> str:
    """Identity set by a trusted gateway; replace with real auth."""
    return x_user_id


ChatDep = Annotated[SupportChat, Depends(get_chat)]
UserDep = Annotated[str, Depends(get_user_id)]


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


@app.post("/conversations", status_code=201)
async def create_conversation(
    chat: ChatDep, user_id: UserDep
) -> Conversation:
    """Start an empty conversation owned by the caller."""
    return await chat.repository.create(user_id)


@app.post("/conversations/{conversation_id}/messages")
async def ask(
    conversation_id: UUID,
    body: QuestionRequest,
    chat: ChatDep,
    user_id: UserDep,
) -> StreamingResponse:
    """Stream the answer to a question, then save the turn."""
    try:
        deltas = await chat.stream(
            user_id,
            conversation_id,
            body.question,
            expected_position=body.expected_position,
        )
    except ConversationNotFound as error:
        raise HTTPException(404, str(error)) from error
    except ConversationConflict as error:
        raise HTTPException(409, str(error)) from error
    return StreamingResponse(deltas, media_type="text/plain")
