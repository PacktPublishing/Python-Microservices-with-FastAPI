from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.session import get_async_session

from .repositories import UserRepository
from .schemas import (
    UserCreate,
    UserListResponse,
    UserRead,
    UserUpdate,
)
from .types import UserRole, UserStatus

router = APIRouter(prefix="/users", tags=["users"])

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]


async def get_user_repo(
    session: SessionDep,
) -> UserRepository:
    """Dependency that provides UserRepository."""
    return UserRepository(session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: UserCreate,
    user_repo: UserRepoDep,
) -> UserRead:
    """Create a new user."""
    try:
        user = await user_repo.create(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    user_repo: UserRepoDep,
) -> UserRead:
    """Get a user by ID."""
    user = await user_repo.get(id=user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.get("/", response_model=UserListResponse)
async def list_users(
    user_repo: UserRepoDep,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
        description="Items per page",
    ),
    role: UserRole | None = Query(
        None,
        description="Filter by role",
    ),
    status_filter: UserStatus | None = Query(
        None,
        alias="status",
        description="Filter by status",
    ),
) -> UserListResponse:
    """Get paginated list of users."""
    skip = (page - 1) * page_size
    filters = {}

    if role:
        filters["role"] = role
    if status_filter:
        filters["status"] = status_filter

    users, total_count = await user_repo.get_multi(
        skip=skip,
        limit=page_size,
        **filters,
    )

    return UserListResponse(
        users=users,
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_repo: UserRepoDep,
) -> UserRead:
    """Update a user."""
    user = await user_repo.update(user_id, user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    user_repo: UserRepoDep,
) -> None:
    """Delete a user."""
    deleted = await user_repo.delete(user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
