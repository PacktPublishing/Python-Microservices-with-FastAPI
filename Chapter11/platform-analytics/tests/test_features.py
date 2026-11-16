import pandas as pd
import pytest

from platform_analytics.data import Tables
from platform_analytics.features import (
    latest_day,
    parent_features,
)


def test_features_ignore_the_future(tables: Tables) -> None:
    """Rows dated after `as_of` do not change the features."""
    as_of = latest_day(tables) - pd.Timedelta(60, unit="D")
    reservations = tables.reservations
    complaints = tables.complaints
    past_only = Tables(
        tables.parents,
        reservations[reservations["starts_at"] <= as_of],
        complaints[complaints["opened_at"] <= as_of],
    )
    pd.testing.assert_frame_equal(
        parent_features(tables, as_of),
        parent_features(past_only, as_of),
    )


def test_features_describe_active_parents(
    current: pd.DataFrame,
) -> None:
    """Every described parent booked in the last 90 days."""
    assert (current["reservations_90d"] > 0).all(), (
        "inactive parents should not be scored"
    )
    assert (current["days_since_last"] < 90).all(), (
        "the last reservation should fall inside the window"
    )


def test_labels_follow_the_horizon(
    tables: Tables,
    labelled: tuple[pd.DataFrame, pd.Series],
    horizon: int,
) -> None:
    """A parent is churned exactly when they do not book in the horizon."""
    features, labels = labelled
    as_of = latest_day(tables) - pd.Timedelta(horizon, unit="D")
    starts = tables.reservations["starts_at"]
    booked = set(
        tables.reservations.loc[starts > as_of, "parent_id"],
    )
    expected = ~features.index.isin(list(booked))
    assert (labels.to_numpy() == expected).all(), (
        "labels should mark parents with no later reservation"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
