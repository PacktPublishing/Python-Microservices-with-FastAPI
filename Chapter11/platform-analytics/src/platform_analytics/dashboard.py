from base64 import b64encode

import polars as pl
from fastapi import FastAPI
from nicegui import ui

from .api import Portal
from .charts import weekly_chart
from .config import ServerSettings


def show(portal: Portal, at_risk: int) -> None:
    """Draw the dashboard of the support team.

    Args:
        portal (Portal):
            The precomputed answers to display.

        at_risk (int):
            How many at-risk parents to list at first.
    """
    chart = b64encode(weekly_chart(portal.weekly)).decode()
    risk = portal.risk.with_columns(pl.col("risk").round(4))
    ui.label("Platform analytics").classes("text-2xl")
    ui.image(f"data:image/png;base64,{chart}").classes("w-full")
    ui.table.from_polars(portal.slots).mark("slots")
    table = ui.table.from_polars(risk.head(at_risk)).mark("risk")
    ui.slider(
        min=1,
        max=100,
        value=at_risk,
        on_change=lambda e: table.update_from_polars(
            risk.head(int(e.value)),
        ),
    )


def mount_dashboard(
    app: FastAPI,
    settings: ServerSettings,
) -> None:
    """Serve the dashboard at `/dashboard` from the API itself.

    Args:
        app (FastAPI):
            The analytics API, whose state holds the portal.

        settings (ServerSettings):
            How many at-risk parents to list at first.
    """
    ui.run_with(
        app,
        root=lambda: show(app.state.portal, settings.at_risk),
        mount_path="/dashboard",
        title="Platform analytics",
        show_welcome_message=False,
    )
