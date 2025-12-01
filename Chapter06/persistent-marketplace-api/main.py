from fastapi import FastAPI

from domain.user.views import router as user_router

app = FastAPI(
    title="Babysitting Marketplace API",
    description="API with PostgreSQL persistence using SQLAlchemy",
    version="0.1.0",
)

app.include_router(user_router)


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
