import numpy as np
import pandas as pd

from .data import Tables

FEATURES = [
    "tenure_days",
    "reservations_90d",
    "days_since_last",
    "cancel_rate",
    "avg_rating",
    "complaints_90d",
]
WINDOW = pd.Timedelta(90, unit="D")


def latest_day(tables: Tables) -> pd.Timestamp:
    """Return the day of the most recent reservation.

    Args:
        tables (Tables):
            The platform's tables.

    Returns:
        pd.Timestamp:
            The day the data ends.
    """
    return tables.reservations["starts_at"].max()


def parent_features(
    tables: Tables,
    as_of: pd.Timestamp,
) -> pd.DataFrame:
    """Describe every parent active in the 90 days before `as_of`.

    Only rows dated on or before `as_of` are read, so the features never see the future.

    Args:
        tables (Tables):
            The platform's tables.

        as_of (pd.Timestamp):
            The day the features describe.

    Returns:
        pd.DataFrame:
            One row per active parent, one column per feature.
    """
    reservations = tables.reservations
    past = reservations[reservations["starts_at"] <= as_of]
    recent = past[past["starts_at"] > as_of - WINDOW]
    by_parent = past.groupby("parent_id")
    bookings_90d = recent["parent_id"].value_counts()
    features = pd.DataFrame(
        {
            "reservations_90d": bookings_90d,
            "days_since_last": (
                as_of - by_parent["starts_at"].max()
            ).dt.days,
            "cancel_rate": past["status"]
            .eq("cancelled")
            .groupby(past["parent_id"])
            .mean(),
            "avg_rating": by_parent["rating"].mean(),
        },
    ).dropna(subset=["reservations_90d"])
    complaints = tables.complaints
    opened = complaints["opened_at"]
    recent_complaints = complaints[
        (opened > as_of - WINDOW) & (opened <= as_of)
    ]
    features["complaints_90d"] = (
        recent_complaints.groupby("parent_id")
        .size()
        .reindex(features.index, fill_value=0)
    )
    parents = tables.parents.set_index("parent_id")
    tenure = as_of - parents["signed_up"]
    features["tenure_days"] = tenure.dt.days
    return features[FEATURES]


def training_set(
    tables: Tables,
    horizon_days: int,
) -> tuple[pd.DataFrame, pd.Series]:
    """Build features and churn labels for a past day.

    A parent has churned when they make no reservation in the `horizon_days` after the day the features describe.

    Args:
        tables (Tables):
            The platform's tables.

        horizon_days (int):
            Days without reservations that count as churn.

    Returns:
        tuple[pd.DataFrame, pd.Series]:
            The features and a boolean label per parent.
    """
    horizon = pd.Timedelta(horizon_days, unit="D")
    as_of = latest_day(tables) - horizon
    features = parent_features(tables, as_of)
    starts = tables.reservations["starts_at"]
    future = tables.reservations[
        (starts > as_of) & (starts <= as_of + horizon)
    ]
    churned = ~features.index.isin(future["parent_id"])
    labels = pd.Series(
        np.asarray(churned),
        index=features.index,
        name="churned",
    )
    return features, labels
