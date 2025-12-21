"""Test fixtures for support chatbot tests."""
import pytest
from unittest.mock import AsyncMock

from domain.support.schemas import ConfidenceLevel, SupportResponse
from domain.support.services import SupportService


@pytest.fixture
def mock_support_service():
    """Provides a mocked support service that doesn't call OpenAI."""
    service = AsyncMock(spec=SupportService)

    async def mock_answer(query):
        return SupportResponse(
            answer="This is a mocked response for testing",
            could_answer=True,
            sources=[],
            confidence=ConfidenceLevel.HIGH,
            suggested_actions=[]
        )

    service.answer_question = mock_answer
    return service
