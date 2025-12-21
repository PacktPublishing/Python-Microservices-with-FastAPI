from enum import Enum

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence levels for agent responses."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SupportQuery(BaseModel):
    """Input schema for support questions."""

    question: str = Field(..., min_length=1)
    conversation_id: str | None = None


class PolicyContext(BaseModel):
    """Context from retrieved policy documents."""

    section: str
    subsection: str
    content: str
    relevance_score: float


class SupportResponse(BaseModel):
    """Output schema for support agent responses."""

    answer: str
    could_answer: bool = Field(
        ...,
        description="Whether the agent could answer the question"
    )
    sources: list[PolicyContext] = Field(default_factory=list)
    confidence: ConfidenceLevel
    suggested_actions: list[str] = Field(default_factory=list)
