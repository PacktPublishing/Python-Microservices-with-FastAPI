from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from .types import UserRole, UserStatus


class UserBase(BaseModel):
    """Base schema for user data."""

    name: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str
    role: UserRole = UserRole.PARENT

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError(
                "Password must be at least 8 characters"
            )
        return v


class UserRead(UserBase):
    """Schema for reading user data."""

    id: int
    role: UserRole
    status: UserStatus
    is_email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for authentication token."""

    access_token: str
    token_type: str = "bearer"
