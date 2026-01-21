from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WeekDaySchema(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TimeSlotSchema(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"


# Request schemas
class CreateSlotRequestSchema(BaseModel):
    week_day: WeekDaySchema
    time_slot: TimeSlotSchema
    babysitter_name: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "week_day": "monday",
                "time_slot": "morning",
                "babysitter_name": "Maria Rodriguez",
            }
        }
    )


class ReserveSlotRequestSchema(BaseModel):
    parent_email: str = Field(..., description="Email of the parent making the reservation")
    description: str = Field("", description="Optional description for the reservation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parent_email": "parent@example.com",
                "description": "Need babysitter for date night",
            }
        }
    )


class SlotResponseSchema(BaseModel):
    id: UUID
    week_day: str
    time_slot: str
    babysitter_name: str
    status: str
    reservation_email: str | None = None
    reservation_description: str | None = None
    reserved_at: datetime | None = None
    confirmed_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "week_day": "monday",
                "time_slot": "morning",
                "babysitter_name": "Maria Rodriguez",
                "status": "available",
                "reservation_email": None,
                "reservation_description": None,
                "reserved_at": None,
                "confirmed_at": None,
            }
        },
    )
