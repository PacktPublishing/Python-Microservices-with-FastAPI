import typing as ty
from datetime import date, timedelta

import polars as pl

from .data import Tables

FEATURES = [
    "tenure_days",
    "reservations_90d",
    "days_since_last",
    "cancel_rate",
    "avg_rating",
    "complaints_90d",
]
WINDOW = timedelta(days=90)


def latest_day(tables: Tables) -> date:
    """Return the day of the last reservation in the data.

    Args:
        tables (Tables):
            The platform's tables.

    Returns:
        date:
            The last day with a reservation.
    """
    return ty.cast(date, tables.reservations["starts_at"].max())


def parent_features(tables: Tables, as_of: date) -> pl.DataFrame:
    """Describe every active parent with rows dated up to `as_of`.

    Args:
        tables (Tables):
            The platform's tables.

        as_of (date):
            The day the features describe; later rows are ignored.

    Returns:
        pl.DataFrame:
            One row per parent with a reservation in the last 90 days.
    """
    starts_at = pl.col("starts_at")
    since = as_of - WINDOW
    bookings = (
        tables.reservations.filter(starts_at <= as_of)
        .group_by("parent_id")
        .agg(
            (starts_at > since).sum().alias("reservations_90d"),
            (as_of - starts_at.max())
            .dt.total_days()
            .alias("days_since_last"),
            (pl.col("status") == "cancelled")
            .mean()
            .alias("cancel_rate"),
            pl.col("rating").mean().alias("avg_rating"),
        )
        .filter(pl.col("reservations_90d") > 0)
    )
    opened_at = pl.col("opened_at")
    complaints = (
        tables.complaints.filter(
            opened_at.is_between(since, as_of, "right"),
        )
        .group_by("parent_id")
        .agg(pl.len().alias("complaints_90d"))
    )
    signed_up = pl.col("signed_up")
    return (
        bookings.join(complaints, on="parent_id", how="left")
        .join(tables.parents, on="parent_id")
        .with_columns(
            pl.col("complaints_90d").fill_null(0),
            (as_of - signed_up)
            .dt.total_days()
            .alias("tenure_days"),
        )
        .select("parent_id", *FEATURES)
        .sort("parent_id")
    )


def training_set(
    tables: Tables,
    horizon_days: int,
) -> tuple[pl.DataFrame, pl.Series]:
    """Build features before the horizon and churn labels after it.

    Args:
        tables (Tables):
            The platform's tables.

        horizon_days (int):
            Days without a reservation that mean churn.

    Returns:
        tuple[pl.DataFrame, pl.Series]:
            The features, and whether each parent churned.
    """
    horizon = timedelta(days=horizon_days)
    as_of = latest_day(tables) - horizon
    features = parent_features(tables, as_of)
    starts_at = pl.col("starts_at")
    future = tables.reservations.filter(
        starts_at.is_between(as_of, as_of + horizon, "right"),
    )
    churned = ~features["parent_id"].is_in(
        future["parent_id"].implode(),
    )
    return features, churned.alias("churned")
