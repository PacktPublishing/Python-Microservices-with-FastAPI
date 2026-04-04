from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field


class Location(BaseModel):
    city: str
    country: str
    latitude: float | None = None
    longitude: float | None = None


class ContactInfo(BaseModel):
    email: EmailStr
    phone: str | None = None


class AvailabilitySlot(BaseModel):
    day: Literal[
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    from_hour: Annotated[
        int, Field(ge=0, le=23, description="Start hour (0–23)")
    ]
    to_hour: Annotated[
        int, Field(ge=0, le=23, description="End hour (0–23)")
    ]
