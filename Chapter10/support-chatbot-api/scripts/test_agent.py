"""Script to test the support agent."""
import asyncio

from domain.support.schemas import SupportQuery
from domain.support.services import SupportService


async def test_agent():
    """Test basic agent functionality."""
    service = SupportService()

    test_queries = [
        "Hello!",
        "Can you help me?",
        "What's your refund policy?",
    ]

    for question in test_queries:
        print(f"\nQuestion: {question}")
        query = SupportQuery(question=question)
        response = await service.answer_question(query)
        print(f"Answer: {response.answer}")
        print(f"Could answer: {response.could_answer}")


async def test_conversation():
    """Test conversation with follow-ups."""
    service = SupportService()
    conv_id = "test-123"

    queries = [
        ("Can I get a refund?", conv_id),
        ("What if it's 48 hours before?", conv_id),
        ("What did you just say?", conv_id),
    ]

    for question, conv in queries:
        print(f"\nUser: {question}")
        query = SupportQuery(question=question, conversation_id=conv)
        response = await service.answer_question(query)
        print(f"Agent: {response.answer}")


if __name__ == "__main__":
    print("=== Testing Basic Agent ===")
    asyncio.run(test_agent())

    print("\n\n=== Testing Conversation ===")
    asyncio.run(test_conversation())
