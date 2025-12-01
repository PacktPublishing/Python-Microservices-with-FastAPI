from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User:
    """Simple user model for demonstration."""

    def __init__(
        self,
        id: int,
        username: str,
        email: str,
        is_active: bool = True,
        role: str = "user",
    ):
        self.id = id
        self.username = username
        self.email = email
        self.is_active = is_active
        self.role = role


class AuthService:
    """Authentication service for user validation."""

    def __init__(self):
        self._mock_users = {
            "testuser": User(
                id=1,
                username="testuser",
                email="test@example.com",
                is_active=True,
                role="parent",
            ),
            "jessica": User(
                id=2,
                username="jessica",
                email="jessica@example.com",
                is_active=True,
                role="sitter",
            ),
            "admin": User(
                id=3,
                username="admin",
                email="admin@example.com",
                is_active=True,
                role="admin",
            ),
        }

    async def authenticate_user(
        self, username: str, password: str
    ) -> User | None:
        """Authenticate user with username and password."""
        if (
            username in self._mock_users
            and password == "password123"
        ):
            return self._mock_users[username]
        return None

    async def get_user_from_token(
        self, token: str
    ) -> User | None:
        """Get user from JWT token (simplified mock)."""
        if token.startswith("mock_token_"):
            username = token.replace("mock_token_", "")
            return self._mock_users.get(username)
        return None

    def create_access_token(self, user: User) -> str:
        """Create access token for user."""
        return f"mock_token_{user.username}"


def get_auth_service() -> AuthService:
    """Dependency that provides auth service."""
    return AuthService()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[
        AuthService, Depends(get_auth_service)
    ],
) -> User:
    """Dependency that provides the current authenticated user."""
    user = await auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
