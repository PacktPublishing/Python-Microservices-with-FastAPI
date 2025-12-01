from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .types import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema with common fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's full name",
    )
    email: EmailStr = Field(
        ...,
        description="User's email address",
    )
    phone: str | None = Field(
        None,
        max_length=20,
        description="Phone number",
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password",
    )
    role: UserRole = Field(
        UserRole.PARENT,
        description="User role in the system",
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
    )
    phone: str | None = Field(
        None,
        max_length=20,
    )
    status: UserStatus | None = None


class UserRead(UserBase):
    """Schema for user data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="User's unique identifier",
    )
    role: UserRole = Field(
        ...,
        description="User role",
    )
    status: UserStatus = Field(
        ...,
        description="Account status",
    )
    is_email_verified: bool = Field(
        ...,
        description="Whether email is verified",
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
    )
    updated_at: datetime | None = Field(
        None,
        description="Last update timestamp",
    )


class UserListResponse(BaseModel):
    """Schema for paginated user list responses."""

    users: list[UserRead]
    total_count: int
    page: int
    page_size: int
