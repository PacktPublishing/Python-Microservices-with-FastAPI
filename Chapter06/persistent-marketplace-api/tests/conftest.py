import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from domain.user.models import ParentProfile, SitterProfile, User
from infrastructure.database.session import (
    Base,
    get_async_session,
)
from main import app

# Ensure models are imported for table creation
_ = User, ParentProfile, SitterProfile


@pytest.fixture
async def sqlite_session():
    """Provides an in-memory SQLite session for fast tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    TestSession = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def client(sqlite_session):
    """Provides a test client with SQLite session override."""

    async def override_get_session():
        yield sqlite_session

    app.dependency_overrides[get_async_session] = (
        override_get_session
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
