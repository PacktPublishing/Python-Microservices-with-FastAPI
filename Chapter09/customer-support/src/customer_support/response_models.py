from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response of the health endpoint."""

    status: str
