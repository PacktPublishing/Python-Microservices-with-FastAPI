import pandas as pd

from .data import SLOTS, Tables

WEEK_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def weekly_activity(reservations: pd.DataFrame) -> pd.DataFrame:
    """Count reservations, confirmation rate and revenue per week.

    Args:
        reservations (pd.DataFrame):
            The reservations table.

    Returns:
        pd.DataFrame:
            One row per week, indexed by the week's last day.
    """
    confirmed = reservations["status"].eq("confirmed")
    revenue = reservations["price"].where(confirmed, 0.0)
    return (
        reservations.assign(confirmed=confirmed, revenue=revenue)
        .groupby(pd.Grouper(key="starts_at", freq="W"))
        .agg(
            reservations=("reservation_id", "size"),
            confirmation_rate=("confirmed", "mean"),
            revenue=("revenue", "sum"),
        )
        .rename_axis("week")
    )


def slot_demand(reservations: pd.DataFrame) -> pd.DataFrame:
    """Count reservations per day of the week and time slot.

    Args:
        reservations (pd.DataFrame):
            The reservations table.

    Returns:
        pd.DataFrame:
            Days of the week as rows, time slots as columns.
    """
    return (
        reservations.assign(
            week_day=reservations["starts_at"].dt.day_name(),
        )
        .pivot_table(
            index="week_day",
            columns="time_slot",
            values="reservation_id",
            aggfunc="size",
            fill_value=0,
        )
        .reindex(index=WEEK_DAYS, columns=SLOTS, fill_value=0)
    )


def complaint_rate(tables: Tables) -> pd.DataFrame:
    """Compute complaints per 100 confirmed reservations per month.

    Args:
        tables (Tables):
            The platform's tables.

    Returns:
        pd.DataFrame:
            One row per month and one column per complaint topic.
    """
    reservations = tables.reservations
    is_confirmed = reservations["status"] == "confirmed"
    confirmed = reservations[is_confirmed]
    per_month = confirmed.groupby(
        confirmed["starts_at"].dt.to_period("M"),
    ).size()
    complaints = tables.complaints
    by_topic = pd.crosstab(
        complaints["opened_at"].dt.to_period("M"),
        complaints["topic"],
    )
    rate = by_topic.div(per_month, axis="index")
    return rate.mul(100).round(2)
