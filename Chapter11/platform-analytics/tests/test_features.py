from datetime import timedelta

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from platform_analytics.data import Complaint, Reservation, Tables
from platform_analytics.features import (
    latest_day,
    parent_features,
)


def test_features_ignore_the_future(tables: Tables) -> None:
    """Rows dated after `as_of` do not change the features."""
    as_of = latest_day(tables) - timedelta(days=60)
    past_only = Tables(
        parents=tables.parents,
        reservations=Reservation.DataFrame(
            tables.reservations.filter(
                pl.col("starts_at") <= as_of,
            ),
        ),
        complaints=Complaint.DataFrame(
            tables.complaints.filter(
                pl.col("opened_at") <= as_of,
            ),
        ),
    )
    assert_frame_equal(
        parent_features(tables, as_of),
        parent_features(past_only, as_of),
    )


def test_features_describe_active_parents(
    current: pl.DataFrame,
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
    labelled: tuple[pl.DataFrame, pl.Series],
    horizon: int,
) -> None:
    """A parent is churned exactly when they do not book in the horizon."""
    features, labels = labelled
    as_of = latest_day(tables) - timedelta(days=horizon)
    booked = tables.reservations.filter(
        pl.col("starts_at") > as_of,
    )
    expected = ~features["parent_id"].is_in(
        booked["parent_id"].implode(),
    )
    assert labels.equals(expected, check_names=False), (
        "labels should mark parents with no later reservation"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
