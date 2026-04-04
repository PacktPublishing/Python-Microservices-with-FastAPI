from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field

from shared.domain.value_objects import (
    AvailabilitySlot,
    ContactInfo,
    Location,
)


class Babysitter(BaseModel):
    """Domain model for a babysitter.

    This is a pure Pydantic model used by all repository
    implementations (MongoDB, TinyDB, etc.).
    """

    id: str | None = None
    first_name: str
    last_name: str
    age: Annotated[
        int, Field(ge=18, description="Must be at least 18")
    ]
    bio: str | None = None
    hourly_rate: Annotated[
        float, Field(gt=0, description="Rate in USD per hour")
    ]
    years_of_experience: Annotated[int, Field(ge=0)]
    languages: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    availability: list[AvailabilitySlot] = Field(
        default_factory=list
    )
    contact: ContactInfo
    location: Location
    is_active: bool = True
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    def refresh_updated_at(self) -> None:
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.now(UTC)
