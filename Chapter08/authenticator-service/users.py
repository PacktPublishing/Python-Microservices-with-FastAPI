from typing import TypedDict

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), unique=True),
    Column("hashed_password", String(255)),
    Column("role", String(50)),
)


class UserRecord(TypedDict):
    email: str
    hashed_password: str
    role: str


async def get_user_by_email(
    db: AsyncSession, email: str
) -> UserRecord | None:
    query = select(
        users.c.email, users.c.hashed_password, users.c.role
    ).where(users.c.email == email)
    result = await db.execute(query)
    row = result.one_or_none()
    if row is None:
        return None
    return UserRecord(
        email=row.email,
        hashed_password=row.hashed_password,
        role=row.role,
    )
