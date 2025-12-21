"""Integration tests for the support agent."""
import os

import pytest

from domain.support.schemas import SupportQuery
from domain.support.services import SupportService

requires_openai = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


@requires_openai
@pytest.mark.asyncio
async def test_agent_answers_refund_question():
    """Integration test: Actually calls OpenAI."""
    service = SupportService()
    query = SupportQuery(
        question="Can I get a refund if the sitter cancels?"
    )

    response = await service.answer_question(query)

    assert response.could_answer is True
    assert response.confidence.value == "high"
    assert len(response.sources) > 0
    assert "refund" in response.answer.lower()


@requires_openai
@pytest.mark.asyncio
async def test_agent_handles_greeting():
    """Integration test: Agent handles greetings without searching."""
    service = SupportService()
    query = SupportQuery(question="Hello!")

    response = await service.answer_question(query)

    assert response.could_answer is True
    assert len(response.sources) == 0


@requires_openai
@pytest.mark.asyncio
async def test_agent_maintains_conversation():
    """Integration test: Agent maintains conversation context."""
    service = SupportService()
    conv_id = "test-conv-123"

    query1 = SupportQuery(
        question="What's your refund policy?",
        conversation_id=conv_id
    )
    response1 = await service.answer_question(query1)

    query2 = SupportQuery(
        question="What about partial refunds?",
        conversation_id=conv_id
    )
    response2 = await service.answer_question(query2)

    assert response1.could_answer is True
    assert response2.could_answer is True
