import pytest
from nicegui import ui
from nicegui.testing import User

from analytics_dashboard.client import ChurnRisk, SlotDemand

pytestmark = pytest.mark.nicegui_main_file("")


async def test_page_shows_the_api_data(
    dashboard: User,
    slots: list[SlotDemand],
    risks: list[ChurnRisk],
    limit: int,
) -> None:
    """The page shows the chart, every day and the riskiest parents."""
    await dashboard.open("/")
    await dashboard.should_see(kind=ui.image)
    rows = [
        row
        for table in dashboard.find(ui.table).elements
        for row in table.rows
    ]
    days = {row.get("week_day") for row in rows}
    parents = {row.get("parent_id") for row in rows}
    assert days >= {slot.week_day for slot in slots}, (
        "the slot table should list every day of the week"
    )
    assert parents == {r.parent_id for r in risks[:limit]} | {
        None,
    }, "only the parents within the initial limit should be shown"


async def test_slider_refreshes_the_parents(
    dashboard: User,
    limits: list[int],
    limit: int,
    new_limit: int,
    caption: str,
) -> None:
    """Moving the slider asks the API again with the new limit."""
    await dashboard.open("/")
    slider = dashboard.find(ui.slider).elements.pop()
    slider.value = new_limit
    dashboard.find(ui.slider).trigger("change")
    await dashboard.should_see(caption.format(new_limit))
    assert limits[0] == limit, (
        "the page should load the initial limit"
    )
    assert limits[-1] == new_limit, (
        "a slider change should fetch the parents for the new limit"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
