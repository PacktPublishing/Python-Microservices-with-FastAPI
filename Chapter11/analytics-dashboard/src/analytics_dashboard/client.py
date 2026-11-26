from base64 import b64encode

import httpx2
from pydantic import BaseModel, TypeAdapter


class SlotDemand(BaseModel):
    """Reservations per time slot on one day of the week."""

    week_day: str
    morning: int
    afternoon: int
    night: int


class ChurnRisk(BaseModel):
    """The estimated probability that a parent churns."""

    parent_id: int
    risk: float


SLOTS = TypeAdapter(list[SlotDemand])
RISKS = TypeAdapter(list[ChurnRisk])


class AnalyticsClient:
    """Read the analytics API on behalf of the dashboard."""

    def __init__(self, client: httpx2.AsyncClient) -> None:
        """Receive the HTTP client rather than creating one.

        Args:
            client (httpx2.AsyncClient):
                Client configured for the analytics API.
        """
        self.client = client

    async def weekly_chart(self) -> str:
        """Return the weekly chart as a data URL for an image.

        Returns:
            str:
                The PNG chart, encoded in base64.
        """
        reply = await self.client.get("/charts/weekly.png")
        reply.raise_for_status()
        encoded = b64encode(reply.content).decode()
        return f"data:image/png;base64,{encoded}"

    async def slots(self) -> list[SlotDemand]:
        """Return the demand per day of the week and time slot.

        Returns:
            list[SlotDemand]:
                One row per day of the week.
        """
        reply = await self.client.get("/activity/slots")
        reply.raise_for_status()
        return SLOTS.validate_json(reply.content)

    async def at_risk(self, limit: int) -> list[ChurnRisk]:
        """Return the active parents most likely to churn.

        Args:
            limit (int):
                How many parents to return.

        Returns:
            list[ChurnRisk]:
                Parents sorted from the highest risk.
        """
        reply = await self.client.get(
            "/parents/at-risk",
            params={"limit": limit},
        )
        reply.raise_for_status()
        return RISKS.validate_json(reply.content)
