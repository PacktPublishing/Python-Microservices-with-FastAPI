from base64 import b64decode

import httpx2
import pytest

from analytics_dashboard.client import (
    AnalyticsClient,
    ChurnRisk,
    SlotDemand,
)


async def test_weekly_chart(
    analytics: AnalyticsClient,
    chart: bytes,
) -> None:
    """The chart comes back as a data URL holding the PNG bytes."""
    url = await analytics.weekly_chart()
    header, encoded = url.split(",")
    assert header == "data:image/png;base64", (
        "the chart should be a base64 PNG data URL"
    )
    assert b64decode(encoded) == chart, (
        "the data URL should hold the API's PNG bytes unchanged"
    )


async def test_slots(
    analytics: AnalyticsClient,
    slots: list[SlotDemand],
) -> None:
    """The slot demand is parsed into models."""
    assert await analytics.slots() == slots, (
        "the client should return the API's slot rows as models"
    )


async def test_at_risk(
    analytics: AnalyticsClient,
    risks: list[ChurnRisk],
    limits: list[int],
    new_limit: int,
) -> None:
    """The client forwards the limit and parses the parents."""
    parents = await analytics.at_risk(new_limit)
    assert limits == [new_limit], "the limit should reach the API"
    assert parents == risks[:new_limit], (
        "the client should return the API's riskiest parents"
    )


async def test_failure(broken: AnalyticsClient) -> None:
    """An API failure is raised, not hidden behind empty data."""
    with pytest.raises(httpx2.HTTPStatusError):
        await broken.slots()


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
