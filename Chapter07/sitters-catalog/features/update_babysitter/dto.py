from typing import Annotated

from pydantic import BaseModel, Field

from shared.domain.value_objects import (
    AvailabilitySlot,
    ContactInfo,
    Location,
)


class UpdateBabysitterDTO(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    age: Annotated[int | None, Field(ge=18)] = None
    bio: str | None = None
    hourly_rate: Annotated[float | None, Field(gt=0)] = None
    years_of_experience: Annotated[int | None, Field(ge=0)] = None
    languages: list[str] | None = None
    certifications: list[str] | None = None
    availability: list[AvailabilitySlot] | None = None
    contact: ContactInfo | None = None
    location: Location | None = None
    is_active: bool | None = None
