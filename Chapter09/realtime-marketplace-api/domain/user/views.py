from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.auth.utils import (
    create_access_token,
    verify_password,
)
from infrastructure.database.session import get_async_session

from .dependencies import get_current_user
from .models import User
from .repositories import UserRepository
from .schemas import Token, UserCreate, UserRead

router = APIRouter(tags=["auth"])


def get_user_repository() -> UserRepository:
    """Get user repository instance."""
    return UserRepository()


@router.post("/auth/register", response_model=UserRead, status_code=201)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session),
    repo: UserRepository = Depends(get_user_repository),
):
    """Register a new user."""
    try:
        user = await repo.create(session, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
    repo: UserRepository = Depends(get_user_repository),
):
    """Login and get access token."""
    user = await repo.get_by_email(session, form_data.username)

    if not user or not verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)


@router.get("/users/me", response_model=UserRead)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Get current user info."""
    return current_user
