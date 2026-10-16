from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from schemas import UserCreate, UserUpdate
from security import hash_password


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalars().first()


async def create_user(
    db: AsyncSession,
    user_in: UserCreate,
) -> User:
    user_data = user_in.model_dump(
        exclude={"password"},
    )
    db_user = User(
        **user_data,
        hashed_password=hash_password(user_in.password),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_by_id(
    db: AsyncSession,
    user_id: int,
) -> User | None:
    return await db.get(User, user_id)


async def update_user(
    db: AsyncSession,
    db_user: User,
    user_in: UserUpdate,
) -> User:
    update_data = user_in.model_dump(
        exclude_unset=True,
    )
    for field, value in update_data.items():
        setattr(db_user, field, value)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def delete_user(
    db: AsyncSession,
    db_user: User,
) -> None:
    await db.delete(db_user)
    await db.commit()
