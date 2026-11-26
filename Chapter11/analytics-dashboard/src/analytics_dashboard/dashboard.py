from nicegui import ui

from .client import AnalyticsClient


def create_dashboard(
    analytics: AnalyticsClient,
    limit: int,
) -> None:
    """Register the dashboard's page.

    Args:
        analytics (AnalyticsClient):
            Client of the analytics API.

        limit (int):
            How many at-risk parents to show at first.
    """

    @ui.page("/")
    async def index() -> None:
        """Show the chart, the slot table and the at-risk parents."""
        ui.label("Platform analytics").classes("text-2xl")
        ui.image(await analytics.weekly_chart()).classes("w-1/2")
        slots = await analytics.slots()
        ui.table(rows=[slot.model_dump() for slot in slots])
        slider = ui.slider(min=1, max=100, value=limit)
        slider.props("label-always")

        @ui.refreshable
        async def at_risk() -> None:
            """Show the riskiest parents for the slider's value."""
            parents = await analytics.at_risk(int(slider.value))
            ui.label(
                f"The {len(parents)} parents most likely to churn",
            )
            ui.table(
                rows=[parent.model_dump() for parent in parents],
            )

        await at_risk()
        slider.on("change", at_risk.refresh)
