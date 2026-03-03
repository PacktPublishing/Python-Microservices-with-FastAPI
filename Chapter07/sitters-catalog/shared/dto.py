from datetime import datetime

from pydantic import BaseModel

from shared.domain.value_objects import (
    AvailabilitySlot,
    ContactInfo,
    Location,
)


class BabysitterResponseDTO(BaseModel):
    id: str
    first_name: str
    last_name: str
    age: int
    bio: str | None = None
    hourly_rate: float
    years_of_experience: int
    languages: list[str]
    certifications: list[str]
    availability: list[AvailabilitySlot]
    contact: ContactInfo
    location: Location
    is_active: bool
    created_at: datetime
    updated_at: datetime
