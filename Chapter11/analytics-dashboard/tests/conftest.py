from collections.abc import AsyncIterator, Iterator
from unittest.mock import MagicMock, patch

import httpx2
import pytest
from nicegui.testing import User

from analytics_dashboard.client import (
    RISKS,
    SLOTS,
    AnalyticsClient,
    ChurnRisk,
    SlotDemand,
)
from analytics_dashboard.config import Settings
from analytics_dashboard.dashboard import create_dashboard

pytest_plugins = ["nicegui.testing.user_plugin"]


@pytest.fixture
def chart() -> bytes:
    """Bytes standing for the PNG chart."""
    return b"\x89PNG chart"


@pytest.fixture
def slots() -> list[SlotDemand]:
    """The demand of two days of the week."""
    return [
        SlotDemand(
            week_day="Monday",
            morning=3,
            afternoon=5,
            night=1,
        ),
        SlotDemand(
            week_day="Tuesday",
            morning=2,
            afternoon=4,
            night=0,
        ),
    ]


@pytest.fixture
def risks() -> list[ChurnRisk]:
    """Three parents, sorted from the highest risk."""
    return [
        ChurnRisk(parent_id=17, risk=0.9),
        ChurnRisk(parent_id=42, risk=0.6),
        ChurnRisk(parent_id=8, risk=0.3),
    ]


@pytest.fixture
def limit() -> int:
    """How many at-risk parents the dashboard shows at first."""
    return 1


@pytest.fixture
def new_limit() -> int:
    """The limit the user picks with the slider."""
    return 3


@pytest.fixture
def limits() -> list[int]:
    """The limits the fake API received, in order."""
    return []


@pytest.fixture
def api(
    chart: bytes,
    slots: list[SlotDemand],
    risks: list[ChurnRisk],
    limits: list[int],
) -> httpx2.MockTransport:
    """A fake analytics API that answers from the fixtures."""

    def handle(request: httpx2.Request) -> httpx2.Response:
        """Answer one request like the analytics API would.

        Args:
            request (httpx2.Request):
                The request sent by the client.

        Returns:
            httpx2.Response:
                The fixture matching the requested path.
        """
        match request.url.path:
            case "/charts/weekly.png":
                return httpx2.Response(200, content=chart)
            case "/activity/slots":
                return httpx2.Response(
                    200,
                    content=SLOTS.dump_json(slots),
                )
            case "/parents/at-risk":
                limits.append(int(request.url.params["limit"]))
                top = risks[: limits[-1]]
                return httpx2.Response(
                    200,
                    content=RISKS.dump_json(top),
                )
        return httpx2.Response(404)

    return httpx2.MockTransport(handle)


@pytest.fixture
async def analytics(
    api: httpx2.MockTransport,
) -> AsyncIterator[AnalyticsClient]:
    """A client of the fake analytics API."""
    async with httpx2.AsyncClient(
        transport=api,
        base_url="http://analytics",
    ) as client:
        yield AnalyticsClient(client)


@pytest.fixture
async def broken() -> AsyncIterator[AnalyticsClient]:
    """A client of an analytics API that always fails."""
    transport = httpx2.MockTransport(
        lambda _: httpx2.Response(500),
    )
    async with httpx2.AsyncClient(
        transport=transport,
        base_url="http://analytics",
    ) as client:
        yield AnalyticsClient(client)


@pytest.fixture
def dashboard(
    user: User,
    analytics: AnalyticsClient,
    limit: int,
) -> User:
    """A simulated user of the dashboard, served by the fake API."""
    create_dashboard(analytics, limit)
    return user


@pytest.fixture
def settings() -> Settings:
    """The dashboard's default settings."""
    return Settings()


@pytest.fixture
def run() -> Iterator[MagicMock]:
    """Replace NiceGUI's server so `main` returns at once."""
    with patch("analytics_dashboard.__main__.ui.run") as run:
        yield run


@pytest.fixture
def caption() -> str:
    """The caption above the at-risk parents, to fill with a count."""
    return "The {} parents most likely to churn"
