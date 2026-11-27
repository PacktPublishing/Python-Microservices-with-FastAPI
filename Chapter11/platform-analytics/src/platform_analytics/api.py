import typing as ty
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

import polars as pl
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
)
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel

from .charts import weekly_chart
from .config import Settings
from .data import FROZEN, Tables
from .exploration import slot_demand, weekly_activity
from .features import latest_day, parent_features
from .model import ChurnModel
from .quality import QualityReport, check_drift


class WeekActivity(BaseModel):
    """Reservations, confirmation rate and revenue of one week."""

    week: date
    reservations: int
    confirmation_rate: float
    revenue: float


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


class Portal(BaseModel):
    """Everything the endpoints read, computed once per refresh."""

    model_config = FROZEN
    weekly: pl.DataFrame
    slots: pl.DataFrame
    risk: pl.DataFrame
    quality: list[QualityReport]


def build_portal(settings: Settings) -> Portal:
    """Load the data and the model, then compute every answer.

    Args:
        settings (Settings):
            Where the data and the model live, and quality thresholds.

    Returns:
        Portal:
            The precomputed answers.
    """
    tables = Tables.load(settings.data.folder)
    model = ChurnModel.load(settings.model.path)
    features = parent_features(tables, latest_day(tables))
    drift = check_drift(
        model.reference,
        features,
        settings.quality,
    )
    logger.info("Portal ready for {} parents", len(features))
    return Portal(
        weekly=weekly_activity(tables.reservations),
        slots=slot_demand(tables.reservations),
        risk=model.risk(features).sort("risk", descending=True),
        quality=[drift],
    )


def get_portal(request: Request) -> Portal:
    """Return the portal stored on the application.

    Args:
        request (Request):
            The current request.

    Returns:
        Portal:
            The precomputed answers.
    """
    portal: Portal = request.app.state.portal
    return portal


PortalDep = ty.Annotated[Portal, Depends(get_portal)]
router = APIRouter()


@router.get("/activity/weekly")
def read_weekly(portal: PortalDep) -> list[WeekActivity]:
    """Return the activity of every week."""
    rows = portal.weekly.to_dicts()
    return [WeekActivity.model_validate(row) for row in rows]


@router.get("/activity/slots")
def read_slots(portal: PortalDep) -> list[SlotDemand]:
    """Return the demand per day of the week and time slot."""
    rows = portal.slots.to_dicts()
    return [SlotDemand.model_validate(row) for row in rows]


@router.get("/charts/weekly.png")
def read_weekly_chart(portal: PortalDep) -> Response:
    """Return the weekly activity as a PNG chart."""
    return Response(
        weekly_chart(portal.weekly),
        media_type="image/png",
    )


@router.get("/parents/at-risk")
def read_at_risk(
    portal: PortalDep,
    limit: ty.Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[ChurnRisk]:
    """Return the active parents most likely to churn."""
    rows = portal.risk.head(limit).to_dicts()
    return [ChurnRisk.model_validate(row) for row in rows]


@router.get("/parents/{parent_id}/risk")
def read_risk(parent_id: int, portal: PortalDep) -> ChurnRisk:
    """Return the churn risk of one active parent."""
    found = portal.risk.filter(pl.col("parent_id") == parent_id)
    if found.is_empty():
        raise HTTPException(404, "Parent is not active")
    return ChurnRisk.model_validate(found.row(0, named=True))


@router.get("/quality")
def read_quality(portal: PortalDep) -> list[QualityReport]:
    """Return the outcome of every data quality check."""
    return portal.quality


def create_app(settings: Settings) -> FastAPI:
    """Create the analytics API.

    Args:
        settings (Settings):
            The service's settings.

    Returns:
        FastAPI:
            The application, which loads its data on startup.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Compute the portal before serving the first request.

        Args:
            app (FastAPI):
                The application being started.
        """
        app.state.portal = build_portal(settings)
        yield

    app = FastAPI(title="Platform analytics", lifespan=lifespan)
    app.include_router(router)
    frontend = StaticFiles(
        directory=settings.server.frontend,
        html=True,
    )
    app.mount("/app", frontend)

    @app.post("/refresh", status_code=204)
    def refresh() -> None:
        """Reload the data and the model, then recompute."""
        app.state.portal = build_portal(settings)

    return app
