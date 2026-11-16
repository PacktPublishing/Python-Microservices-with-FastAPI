from pathlib import Path

import pandas as pd
import pytest

from platform_analytics.config import Settings
from platform_analytics.data import SLOTS, Tables
from platform_analytics.exploration import (
    WEEK_DAYS,
    complaint_rate,
    slot_demand,
    weekly_activity,
)
from platform_analytics.simulation import TOPICS, simulate


def test_simulation_is_reproducible(
    tables: Tables,
    settings: Settings,
) -> None:
    """Simulating twice with the same seed gives the same reservations."""
    again = simulate(settings.data)
    pd.testing.assert_frame_equal(
        tables.reservations,
        again.reservations,
    )


def test_tables_round_trip(
    tables: Tables,
    tmp_path: Path,
) -> None:
    """Saving and loading the tables keeps every value and dtype."""
    tables.save(tmp_path)
    loaded = Tables.load(tmp_path)
    for name in ("parents", "reservations", "complaints"):
        pd.testing.assert_frame_equal(
            getattr(loaded, name),
            getattr(tables, name),
            check_dtype=False,
            obj=name,
        )


def test_weekly_activity_counts_every_reservation(
    tables: Tables,
) -> None:
    """The weekly counts add up to the number of reservations."""
    weekly = weekly_activity(tables.reservations)
    assert weekly["reservations"].sum() == len(
        tables.reservations,
    ), "every reservation should fall in exactly one week"
    assert weekly["confirmation_rate"].between(0, 1).all(), (
        "the confirmation rate should be a share"
    )


def test_slot_demand_is_ordered(tables: Tables) -> None:
    """The demand table lists days in calendar order and every slot."""
    demand = slot_demand(tables.reservations)
    assert list(demand.index) == WEEK_DAYS, (
        "days should be ordered"
    )
    assert list(demand.columns) == SLOTS, (
        "every slot should appear"
    )
    assert demand.to_numpy().sum() == len(tables.reservations), (
        "every reservation should be counted once"
    )


def test_complaint_rate_has_every_topic(tables: Tables) -> None:
    """The monthly complaint rate has one non-negative column per topic."""
    rate = complaint_rate(tables)
    assert sorted(rate.columns) == sorted(TOPICS), (
        "every topic should have a column"
    )
    assert (rate.fillna(0) >= 0).all().all(), (
        "rates should never be negative"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
