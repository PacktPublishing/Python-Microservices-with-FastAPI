from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from .schemas import UserCreate, UserUpdate


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user_dict = user_data.model_dump()
        user_dict["hashed_password"] = (
            f"hashed_{user_dict.pop('password')}"
        )
        new_user = User(**user_dict)

        try:
            self.session.add(new_user)
            await self.session.commit()
            await self.session.refresh(new_user)
            return new_user
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("Email already exists")

    async def get(self, **kwargs: Any) -> User | None:
        """Get a user by filters."""
        stmt = select(User)

        for key, value in kwargs.items():
            if hasattr(User, key):
                stmt = stmt.where(getattr(User, key) == value)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        **kwargs: Any,
    ) -> tuple[list[User], int]:
        """Get multiple users with pagination."""
        stmt = select(User)
        count_stmt = select(func.count()).select_from(User)

        for key, value in kwargs.items():
            if hasattr(User, key):
                filter_condition = getattr(User, key) == value
                stmt = stmt.where(filter_condition)
                count_stmt = count_stmt.where(filter_condition)

        total_count = await self.session.scalar(count_stmt) or 0

        stmt = (
            stmt.offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )

        result = await self.session.execute(stmt)
        users = result.scalars().all()

        return list(users), total_count

    async def update(
        self,
        user_id: int,
        user_data: UserUpdate,
    ) -> User | None:
        """Update a user."""
        update_data = user_data.model_dump(exclude_unset=True)

        if not update_data:
            return await self.get(id=user_id)

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User)
        )

        result = await self.session.execute(stmt)
        updated_user = result.scalar_one_or_none()

        if updated_user:
            await self.session.commit()
            await self.session.refresh(updated_user)

        return updated_user

    async def delete(self, user_id: int) -> bool:
        """Delete a user."""
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)

        if result.rowcount > 0:
            await self.session.commit()
            return True
        return False

    async def exists(self, **kwargs: Any) -> bool:
        """Check if a user exists."""
        stmt = select(User.id)

        for key, value in kwargs.items():
            if hasattr(User, key):
                stmt = stmt.where(getattr(User, key) == value)

        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count(self, **kwargs: Any) -> int:
        """Count users matching filters."""
        stmt = select(func.count()).select_from(User)

        for key, value in kwargs.items():
            if hasattr(User, key):
                stmt = stmt.where(getattr(User, key) == value)

        result = await self.session.execute(stmt)
        return result.scalar() or 0


async def get_user_repository(
    session: AsyncSession,
) -> UserRepository:
    """Dependency that provides a UserRepository instance."""
    return UserRepository(session)
