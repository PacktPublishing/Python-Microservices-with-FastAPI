from fastapi import FastAPI

from .response_models import HealthResponse

app = FastAPI(title="Customer Support")


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")
