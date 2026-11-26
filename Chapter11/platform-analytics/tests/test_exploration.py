from pathlib import Path

import pytest
from polars.testing import assert_frame_equal

from platform_analytics.config import Settings
from platform_analytics.data import SLOTS, TOPICS, Tables
from platform_analytics.exploration import (
    complaint_rate,
    slot_demand,
    weekly_activity,
)
from platform_analytics.simulation import simulate


def test_simulation_is_reproducible(
    tables: Tables,
    settings: Settings,
) -> None:
    """Simulating twice with the same seed gives the same reservations."""
    again = simulate(settings.data)
    assert_frame_equal(
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
    for table, again in (
        (tables.parents, loaded.parents),
        (tables.reservations, loaded.reservations),
        (tables.complaints, loaded.complaints),
    ):
        assert_frame_equal(again, table)


def test_weekly_activity_counts_every_reservation(
    tables: Tables,
) -> None:
    """The weekly counts add up to the number of reservations."""
    weekly = weekly_activity(tables.reservations)
    assert weekly["reservations"].sum() == len(
        tables.reservations,
    ), "every reservation should fall in exactly one week"
    assert weekly["confirmation_rate"].is_between(0, 1).all(), (
        "the confirmation rate should be a share"
    )


def test_slot_demand_is_ordered(
    tables: Tables,
    week_days: list[str],
) -> None:
    """The demand table lists days in calendar order and every slot."""
    demand = slot_demand(tables.reservations)
    assert demand["week_day"].to_list() == week_days, (
        "days should be ordered"
    )
    assert demand.columns == ["week_day", *SLOTS], (
        "every slot should appear"
    )
    counts = demand.select(SLOTS).sum_horizontal().sum()
    assert counts == len(tables.reservations), (
        "every reservation should be counted once"
    )


def test_complaint_rate_has_every_topic(tables: Tables) -> None:
    """The monthly complaint rate has one non-negative column per topic."""
    rate = complaint_rate(tables)
    assert rate.columns == ["month", *TOPICS], (
        "every topic should have a column"
    )
    assert (rate.select(TOPICS).min_horizontal() >= 0).all(), (
        "rates should never be negative"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
