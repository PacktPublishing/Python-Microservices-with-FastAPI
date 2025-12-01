from fastapi import FastAPI

from app.routers import parents_router, sitters_router

app = FastAPI(
    title="Babysitting Marketplace API",
    description="API demonstrating Dependency Injection patterns",
    version="0.1.0",
)

app.include_router(sitters_router)
app.include_router(parents_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Babysitting Marketplace API",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
