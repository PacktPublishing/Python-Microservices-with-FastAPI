from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

load_dotenv()

from infrastructure.vector.store import get_vector_store

from .schemas import ConfidenceLevel, PolicyContext, SupportResponse


class ConversationState:
    """Maintains conversation history for context."""

    def __init__(self):
        self.history: list[tuple[str, str]] = []

    def add_turn(self, question: str, answer: str):
        """Add a conversation turn to history."""
        self.history.append((question, answer))

    def get_context(self) -> str:
        """Get formatted conversation context."""
        if not self.history:
            return ""

        context = "Previous conversation:\n"
        for q, a in self.history[-3:]:
            context += f"User: {q}\nAssistant: {a}\n\n"
        return context


support_agent = Agent(
    'openai:gpt-4o',
    output_type=SupportResponse,
    deps_type=ConversationState,
    system_prompt="""You are a helpful support agent for a babysitting marketplace.

Your job is to answer questions about marketplace policies.

Conversation Context:
- Use the conversation history to understand follow-up questions
- Reference previous answers when relevant
- Don't repeat searches if you already have the information

When to search policies:
- User asks about specific policies (refunds, payments, safety, etc.)
- User needs factual information about platform rules
- User asks "what if" questions about scenarios

When NOT to search:
- Greetings and thank you messages
- General "can you help" requests
- Clarification about your previous answers
- Small talk

Tool Usage:
- Call search_policies with keywords from policy questions
- If search returns relevant policies (relevance_score > 0.6), use them
- If search returns nothing relevant, set could_answer=false

Response Format:
- answer (str): Natural conversational response
- could_answer (bool): true if you answered, false if you need more info
- sources (list): Include PolicyContext objects when you searched
- confidence (str): high, medium, or low
- suggested_actions (list[str]): Next steps for the user (optional)
"""
)


@support_agent.tool
async def search_policies(
    ctx: RunContext[ConversationState],
    query: str
) -> list[PolicyContext]:
    """Search marketplace policies for specific information.

    Args:
        query: Keywords from the question like "refund", "payment", "emergency"

    Returns:
        List of relevant policy sections with relevance scores.
        Scores above 0.6 are relevant, below may not be useful.
    """
    store = get_vector_store()
    results = store.search(query, n_results=3)

    policies = []
    for result in results:
        policies.append(PolicyContext(
            section=result['metadata'].get('section', 'Unknown'),
            subsection=result['metadata'].get('subsection', 'Unknown'),
            content=result['text'],
            relevance_score=1.0 - (result['distance'] / 2.0)
        ))

    return policies
