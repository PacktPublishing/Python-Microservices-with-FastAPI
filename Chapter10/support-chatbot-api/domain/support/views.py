from fastapi import APIRouter, Depends

from domain.support.schemas import SupportQuery, SupportResponse
from domain.support.services import SupportService

router = APIRouter(prefix="/support", tags=["support"])


def get_support_service() -> SupportService:
    """Dependency that provides the support service."""
    return SupportService()


@router.post("/chat", response_model=SupportResponse)
async def chat(
    query: SupportQuery,
    service: SupportService = Depends(get_support_service)
) -> SupportResponse:
    """Send a question to the support chatbot."""
    return await service.answer_question(query)
