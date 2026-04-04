from typing import Annotated

from pydantic import BaseModel, Field

from shared.domain.value_objects import (
    AvailabilitySlot,
    ContactInfo,
    Location,
)


class CreateBabysitterDTO(BaseModel):
    first_name: str
    last_name: str
    age: Annotated[int, Field(ge=18)]
    bio: str | None = None
    hourly_rate: Annotated[float, Field(gt=0)]
    years_of_experience: Annotated[int, Field(ge=0)]
    languages: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    availability: list[AvailabilitySlot] = Field(
        default_factory=list
    )
    contact: ContactInfo
    location: Location
