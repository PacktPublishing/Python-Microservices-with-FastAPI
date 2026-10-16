import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from database import DATABASE_URL


async def main() -> None:
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        version = await conn.scalar(text("SELECT version()"))
    await engine.dispose()
    print(f"Connected to: {version}")


asyncio.run(main())
