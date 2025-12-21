from fastapi import FastAPI

from domain.support.views import router as support_router

app = FastAPI(
    title="Support Chatbot API",
    description="AI-powered support chatbot using RAG and PydanticAI",
    version="1.0.0",
)

app.include_router(support_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Support Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
