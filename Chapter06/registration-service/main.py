from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import crud
from database import engine, get_db
from models import User
from schemas import UserCreate, UserResponse, UserUpdate

DbSession = Annotated[AsyncSession, Depends(get_db)]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title="Registration Service",
    lifespan=lifespan,
)


@app.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_in: UserCreate,
    db: DbSession,
) -> User:
    existing = await crud.get_user_by_email(
        db,
        email=user_in.email,
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )
    return await crud.create_user(db, user_in=user_in)


async def get_user_or_404(
    user_id: int,
    db: DbSession,
) -> User:
    user = await crud.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


CurrentUser = Annotated[User, Depends(get_user_or_404)]


@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
)
async def read_user(user: CurrentUser) -> User:
    return user


@app.patch(
    "/users/{user_id}",
    response_model=UserResponse,
)
async def edit_user(
    user: CurrentUser,
    user_in: UserUpdate,
    db: DbSession,
) -> User:
    return await crud.update_user(
        db,
        db_user=user,
        user_in=user_in,
    )


@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_user(
    user: CurrentUser,
    db: DbSession,
) -> None:
    await crud.delete_user(db, db_user=user)
