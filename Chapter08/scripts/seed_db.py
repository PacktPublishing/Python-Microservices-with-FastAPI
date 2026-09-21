# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "sqlalchemy[asyncio]",
#     "aiosqlite",
#     "pwdlib[argon2]",
# ]
# ///

import asyncio

from pwdlib import PasswordHash
from sqlalchemy import String
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

DATABASE_URL = "sqlite+aiosqlite:///./auth_users.db"

engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        db.add_all(
            [
                # User(
                #     email="sofia.ricci@example.com",
                #     hashed_password=hash_password(
                #         "aVeryStrongPassword"
                #     ),
                #     role="parent",
                # ),
                # User(
                #     email="marco.bianchi@example.com",
                #     hashed_password=hash_password(
                #         "anotherStrongPassword"
                #     ),
                #     role="babysitter",
                # ),
                User(
                    email="giuniodl@live.it",
                    hashed_password=hash_password("coco"),
                    role="babysitter",
                ),
            ]
        )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
