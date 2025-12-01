from datetime import datetime

from pydantic import BaseModel, field_validator

from .types import BookingStatus


class BookingBase(BaseModel):
    """Base schema for bookings."""

    sitter_id: int
    start_time: datetime
    end_time: datetime
    hourly_rate: float | None = None
    notes: str | None = None

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        start = info.data.get("start_time")
        if start and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class BookingCreate(BookingBase):
    """Schema for creating a booking."""

    pass


class BookingRead(BookingBase):
    """Schema for reading a booking."""

    id: int
    parent_id: int
    status: BookingStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class BookingUpdate(BaseModel):
    """Schema for updating a booking."""

    start_time: datetime | None = None
    end_time: datetime | None = None
    hourly_rate: float | None = None
    notes: str | None = None
