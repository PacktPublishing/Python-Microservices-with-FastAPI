from abc import ABC, abstractmethod
from typing import Literal
from uuid import UUID, uuid4

import httpx

WeekDay = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]
TimeSlot = Literal["morning", "afternoon", "night"]
SlotStatus = Literal["available", "pending", "confirmed", "refused"]


class ReservationClientInterface(ABC):
    @abstractmethod
    async def list_slots(
        self,
        week_day: WeekDay | None = None,
        time_slot: TimeSlot | None = None,
    ) -> list[dict]:
        """List available slots with optional filtering."""
        ...

    @abstractmethod
    async def reserve_slot(
        self,
        slot_id: UUID,
        parent_email: str,
        description: str = "",
    ) -> dict:
        """Reserve a slot for a parent."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the reservation service is healthy."""
        ...


class ReservationClient(ReservationClientInterface):
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url

    async def list_slots(
        self,
        week_day: WeekDay | None = None,
        time_slot: TimeSlot | None = None,
    ) -> list[dict]:
        async with httpx.AsyncClient() as client:
            params = {}
            if week_day:
                params["week_day"] = week_day
            if time_slot:
                params["time_slot"] = time_slot
            response = await client.get(
                f"{self.base_url}/api/v1/slots",
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def reserve_slot(
        self,
        slot_id: UUID,
        parent_email: str,
        description: str = "",
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/slots/{slot_id}/reserve",
                json={
                    "parent_email": parent_email,
                    "description": description,
                },
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.RequestError:
            return False


class MockReservationClient(ReservationClientInterface):
    def __init__(self):
        self.slots: dict[UUID, dict] = {}
        self.is_healthy = True

    async def list_slots(
        self,
        week_day: WeekDay | None = None,
        time_slot: TimeSlot | None = None,
    ) -> list[dict]:
        result = list(self.slots.values())
        if week_day:
            result = [s for s in result if s["week_day"] == week_day]
        if time_slot:
            result = [s for s in result if s["time_slot"] == time_slot]
        return result

    async def reserve_slot(
        self,
        slot_id: UUID,
        parent_email: str,
        description: str = "",
    ) -> dict:
        if slot_id not in self.slots:
            raise ValueError(f"Slot {slot_id} not found")
        slot = self.slots[slot_id]
        if slot["status"] != "available":
            raise ValueError(f"Slot {slot_id} is not available")
        slot["status"] = "pending"
        slot["parent_email"] = parent_email
        slot["description"] = description
        return slot

    async def health_check(self) -> bool:
        return self.is_healthy
