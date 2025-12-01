from enum import Enum


class UserRole(Enum):
    """User role in the marketplace."""

    PARENT = "parent"
    SITTER = "sitter"
    ADMIN = "admin"


class UserStatus(Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
