import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from domain.user.models import User
from domain.user.types import UserRole
from infrastructure.auth.utils import create_access_token, get_password_hash
from infrastructure.celery.celery_app import celery_app
from infrastructure.database.session import Base, get_async_session

from domain.bookings.models import Booking  # noqa: F401
from domain.notifications.models import Notification  # noqa: F401


@pytest.fixture
def celery_config():
    """Configure Celery for eager execution in tests."""
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )
    yield
    celery_app.conf.update(
        task_always_eager=False,
        task_eager_propagates=False,
    )


_test_engine = None
_test_session_factory = None


@pytest.fixture
async def sqlite_session():
    """Create an in-memory SQLite session for testing."""
    global _test_engine, _test_session_factory

    _test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    _test_session_factory = async_sessionmaker(
        bind=_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with _test_session_factory() as session:
        yield session

    await _test_engine.dispose()
    _test_engine = None
    _test_session_factory = None


@pytest.fixture
async def test_parent(sqlite_session: AsyncSession) -> User:
    """Create a test parent user."""
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        name="Test Parent",
        email=f"parent_{unique_id}@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.PARENT,
    )
    sqlite_session.add(user)
    await sqlite_session.commit()
    await sqlite_session.refresh(user)
    return user


@pytest.fixture
async def test_sitter(sqlite_session: AsyncSession) -> User:
    """Create a test sitter user."""
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        name="Test Sitter",
        email=f"sitter_{unique_id}@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.SITTER,
    )
    sqlite_session.add(user)
    await sqlite_session.commit()
    await sqlite_session.refresh(user)
    return user


@pytest.fixture
async def parent_token(test_parent: User) -> str:
    """Create JWT token for test parent."""
    return create_access_token(data={"sub": str(test_parent.id)})


@pytest.fixture
async def sitter_token(test_sitter: User) -> str:
    """Create JWT token for test sitter."""
    return create_access_token(data={"sub": str(test_sitter.id)})


@pytest.fixture
async def client(sqlite_session: AsyncSession):
    """Create async test client with overridden database."""
    from main import app

    global _test_session_factory

    async def override_get_session():
        async with _test_session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
