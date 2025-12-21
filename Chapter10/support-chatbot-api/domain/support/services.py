from .agent import ConversationState, support_agent
from .schemas import SupportQuery, SupportResponse


class SupportService:
    """Service layer for support chatbot."""

    def __init__(self):
        self.conversations: dict[str, ConversationState] = {}

    async def answer_question(
        self,
        query: SupportQuery
    ) -> SupportResponse:
        """Answer a support question using the AI agent."""
        conv_id = query.conversation_id or "default"
        if conv_id not in self.conversations:
            self.conversations[conv_id] = ConversationState()

        state = self.conversations[conv_id]

        prompt = query.question
        if state.history:
            prompt = f"{state.get_context()}\nUser: {query.question}"

        result = await support_agent.run(prompt, deps=state)
        response = result.output

        state.add_turn(query.question, response.answer)

        return response
