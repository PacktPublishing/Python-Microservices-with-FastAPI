from fastapi import FastAPI

from .response_models import HealthResponse

app = FastAPI(title="Customer Support")


@app.get("/health")
def health() -> HealthResponse:
    """Report that the service is up."""
    return HealthResponse(status="ok")
