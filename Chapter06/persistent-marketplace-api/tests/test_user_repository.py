import pytest

from domain.user.repositories import UserRepository
from domain.user.schemas import UserCreate, UserUpdate
from domain.user.types import UserRole, UserStatus


@pytest.mark.asyncio
async def test_create_user(sqlite_session):
    """Test creating a user via repository."""
    repo = UserRepository(sqlite_session)
    user_data = UserCreate(
        name="Test User",
        email="test@example.com",
        password="password123",
    )

    user = await repo.create(user_data)

    assert user.id is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.hashed_password.startswith("hashed_")
    assert user.role == UserRole.PARENT
    assert user.status == UserStatus.ACTIVE


@pytest.mark.asyncio
async def test_create_user_duplicate_email(sqlite_session):
    """Test that creating user with duplicate email fails."""
    repo = UserRepository(sqlite_session)
    user_data = UserCreate(
        name="Test User",
        email="duplicate@example.com",
        password="password123",
    )

    await repo.create(user_data)

    with pytest.raises(ValueError, match="Email already exists"):
        await repo.create(user_data)


@pytest.mark.asyncio
async def test_get_user_by_id(sqlite_session):
    """Test getting a user by ID."""
    repo = UserRepository(sqlite_session)
    user_data = UserCreate(
        name="Test User",
        email="test@example.com",
        password="password123",
    )
    created_user = await repo.create(user_data)

    found_user = await repo.get(id=created_user.id)

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email(sqlite_session):
    """Test getting a user by email."""
    repo = UserRepository(sqlite_session)
    user_data = UserCreate(
        name="Test User",
        email="test@example.com",
        password="password123",
    )
    await repo.create(user_data)

    found_user = await repo.get(email="test@example.com")

    assert found_user is not None
    assert found_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(sqlite_session):
    """Test getting a non-existent user returns None."""
    repo = UserRepository(sqlite_session)

    found_user = await repo.get(id=99999)

    assert found_user is None


@pytest.mark.asyncio
async def test_get_multi_users(sqlite_session):
    """Test getting multiple users with pagination."""
    repo = UserRepository(sqlite_session)

    for i in range(5):
        await repo.create(
            UserCreate(
                name=f"User {i}",
                email=f"user{i}@example.com",
                password="password123",
            )
        )

    users, total = await repo.get_multi(skip=0, limit=3)

    assert len(users) == 3
    assert total == 5


@pytest.mark.asyncio
async def test_get_multi_with_filter(sqlite_session):
    """Test getting users with role filter."""
    repo = UserRepository(sqlite_session)

    await repo.create(
        UserCreate(
            name="Parent User",
            email="parent@example.com",
            password="password123",
            role=UserRole.PARENT,
        )
    )
    await repo.create(
        UserCreate(
            name="Sitter User",
            email="sitter@example.com",
            password="password123",
            role=UserRole.SITTER,
        )
    )

    parents, total = await repo.get_multi(role=UserRole.PARENT)

    assert len(parents) == 1
    assert total == 1
    assert parents[0].role == UserRole.PARENT


@pytest.mark.asyncio
async def test_update_user(sqlite_session):
    """Test updating a user."""
    repo = UserRepository(sqlite_session)
    user_data = UserCreate(
        name="Original Name",
        email="test@example.com",
        password="password123",
    )
    user = await repo.create(user_data)

    update_data = UserUpdate(name="Updated Name")
    updated_user = await repo.update(user.id, update_data)

    assert updated_user is not None
    assert updated_user.name == "Updated Name"
    assert updated_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_update_user_not_found(sqlite_session):
    """Test updating a non-existent user returns None."""
    repo = UserRepository(sqlite_session)

    update_data = UserUpdate(name="New Name")
    result = await repo.update(99999, update_data)

    assert result is None


@pytest.mark.asyncio
async def test_delete_user(sqlite_session):
    """Test deleting a user."""
    repo = UserRepository(sqlite_session)
    user_data = UserCreate(
        name="Test User",
        email="test@example.com",
        password="password123",
    )
    user = await repo.create(user_data)

    deleted = await repo.delete(user.id)

    assert deleted is True
    assert await repo.get(id=user.id) is None


@pytest.mark.asyncio
async def test_delete_user_not_found(sqlite_session):
    """Test deleting a non-existent user returns False."""
    repo = UserRepository(sqlite_session)

    deleted = await repo.delete(99999)

    assert deleted is False


@pytest.mark.asyncio
async def test_user_exists(sqlite_session):
    """Test checking if user exists."""
    repo = UserRepository(sqlite_session)
    user_data = UserCreate(
        name="Test User",
        email="test@example.com",
        password="password123",
    )
    await repo.create(user_data)

    assert await repo.exists(email="test@example.com") is True
    assert (
        await repo.exists(email="nonexistent@example.com")
        is False
    )


@pytest.mark.asyncio
async def test_count_users(sqlite_session):
    """Test counting users."""
    repo = UserRepository(sqlite_session)

    for i in range(3):
        await repo.create(
            UserCreate(
                name=f"User {i}",
                email=f"user{i}@example.com",
                password="password123",
            )
        )

    count = await repo.count()

    assert count == 3
