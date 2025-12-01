from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.auth.utils import get_password_hash

from .models import User
from .schemas import UserCreate


class UserRepository:
    """Repository for user database operations."""

    async def create(
        self,
        session: AsyncSession,
        user_data: UserCreate,
    ) -> User:
        """Create a new user."""
        hashed_password = get_password_hash(user_data.password)
        user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_password,
            role=user_data.role,
        )

        try:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except IntegrityError:
            await session.rollback()
            raise ValueError("Email already exists")

    async def get(
        self,
        session: AsyncSession,
        **kwargs: Any,
    ) -> User | None:
        """Get a user by filters."""
        stmt = select(User)

        for key, value in kwargs.items():
            if hasattr(User, key):
                stmt = stmt.where(getattr(User, key) == value)

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> User | None:
        """Get a user by email."""
        return await self.get(session, email=email)
