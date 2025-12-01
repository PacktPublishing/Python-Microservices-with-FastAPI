from enum import Enum


class UserRole(str, Enum):
    """User roles in the marketplace."""

    PARENT = "parent"
    SITTER = "sitter"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
