from contextlib import asynccontextmanager

from fastapi import FastAPI

from domain.bookings.views import router as bookings_router
from domain.notifications.views import router as notifications_router
from domain.user.views import router as auth_router
from infrastructure.websocket.connection_manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Start Redis pub/sub listener
    await manager.start_listening()
    yield
    # Shutdown: Clean up connections
    await manager.shutdown()


app = FastAPI(
    title="Realtime Marketplace API",
    description=(
        "Marketplace API with background tasks, "
        "WebSockets, and real-time notifications"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(auth_router)
app.include_router(bookings_router)
app.include_router(notifications_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Realtime Marketplace API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
