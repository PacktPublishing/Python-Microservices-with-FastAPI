from enum import Enum
from dataclasses import dataclass


class WeekDay(Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TimeSlot(Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"


@dataclass(frozen=True)
class BabysitterInfo:
    name: str

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Babysitter name cannot be empty")


class SlotStatus(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    CONFIRMED = "confirmed"


@dataclass(frozen=True)
class ReservationRequest:
    email: str
    description: str = ""

    def __post_init__(self):
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email address")
