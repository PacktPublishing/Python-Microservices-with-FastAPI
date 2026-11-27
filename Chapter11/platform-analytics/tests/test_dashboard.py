import pytest
from nicegui import ui
from nicegui.testing import user_simulation

from platform_analytics.api import Portal
from platform_analytics.dashboard import show


async def test_dashboard_lists_parents_at_risk(
    portal: Portal,
    limit: int,
    week_days: list[str],
) -> None:
    """The page shows the slot table and the riskiest parents."""
    async with user_simulation(
        lambda: show(portal, limit),
    ) as user:
        await user.open("/")
        (slots,) = user.find(
            kind=ui.table,
            marker="slots",
        ).elements
        (risky,) = user.find(
            kind=ui.table,
            marker="risk",
        ).elements
        assert len(slots.rows) == len(week_days), (
            "the slot table should have one row per day"
        )
        assert len(risky.rows) == limit, (
            "the risk table should start with `at_risk` parents"
        )


async def test_slider_changes_parents_shown(
    portal: Portal,
    limit: int,
    more: int,
) -> None:
    """Moving the slider lists more parents."""
    async with user_simulation(
        lambda: show(portal, limit),
    ) as user:
        await user.open("/")
        (slider,) = user.find(ui.slider).elements
        slider.value = more
        (risky,) = user.find(
            kind=ui.table,
            marker="risk",
        ).elements
        assert len(risky.rows) == more, (
            "the risk table should follow the slider"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
