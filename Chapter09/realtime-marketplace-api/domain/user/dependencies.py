from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.auth.utils import decode_token
from infrastructure.database.session import get_async_session

from .models import User
from .repositories import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    repo = UserRepository()
    user = await repo.get(session, id=user_id)
    if user is None:
        raise credentials_exception

    return user


async def get_user_from_token(
    token: str,
    session: AsyncSession,
) -> User:
    """Validate JWT token and return user (for WebSockets)."""
    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise ValueError("Invalid token payload")
        user_id = int(user_id_str)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid token: {e}")

    repo = UserRepository()
    user = await repo.get(session, id=user_id)
    if not user:
        raise ValueError("User not found")

    return user
