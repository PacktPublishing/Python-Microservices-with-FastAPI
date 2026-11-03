from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response of the health endpoint."""

    status: str


class QuestionRequest(BaseModel):
    """A question and the history length it was asked against."""

    question: str = Field(min_length=1)
    expected_position: int = Field(ge=0)
