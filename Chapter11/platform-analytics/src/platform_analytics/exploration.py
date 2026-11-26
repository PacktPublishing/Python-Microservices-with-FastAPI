import polars as pl

from .data import SLOTS, TOPICS, Tables

CONFIRMED = pl.col("status") == "confirmed"


def weekly_activity(reservations: pl.DataFrame) -> pl.DataFrame:
    """Summarize reservations, confirmations and revenue per week.

    Args:
        reservations (pl.DataFrame):
            The reservations table.

    Returns:
        pl.DataFrame:
            One row per week, labelled by its Sunday.
    """
    week = (
        pl.col("starts_at").dt.truncate("1w").dt.offset_by("6d")
    )
    return (
        reservations.group_by(week.alias("week"))
        .agg(
            pl.len().alias("reservations"),
            CONFIRMED.mean().alias("confirmation_rate"),
            pl.col("price")
            .filter(CONFIRMED)
            .sum()
            .alias("revenue"),
        )
        .sort("week")
    )


def slot_demand(reservations: pl.DataFrame) -> pl.DataFrame:
    """Count reservations per day of the week and time slot.

    Args:
        reservations (pl.DataFrame):
            The reservations table.

    Returns:
        pl.DataFrame:
            One row per day, from Monday, and one column per slot.
    """
    starts_at = pl.col("starts_at")
    day = starts_at.dt.weekday().alias("day")
    day_name = starts_at.first().dt.strftime("%A")
    slot = pl.col("time_slot")
    return (
        reservations.group_by(day)
        .agg(
            day_name.alias("week_day"),
            *[(slot == s).sum().alias(s) for s in SLOTS],
        )
        .sort("day")
        .drop("day")
    )


def month_of(column: str) -> pl.Expr:
    """Move each date of `column` to the first day of its month.

    Args:
        column (str):
            A column of dates.

    Returns:
        pl.Expr:
            The months, in a column named `month`.
    """
    return pl.col(column).dt.truncate("1mo").alias("month")


def complaint_rate(tables: Tables) -> pl.DataFrame:
    """Compute complaints per 100 confirmed reservations, per month.

    Args:
        tables (Tables):
            The reservations and the complaints.

    Returns:
        pl.DataFrame:
            One row per month and one column per complaint topic.
    """
    confirmed = (
        tables.reservations.filter(CONFIRMED)
        .group_by(month_of("starts_at"))
        .agg(pl.len().alias("confirmed"))
    )
    topic = pl.col("topic")
    rates = pl.col(TOPICS) / pl.col("confirmed") * 100
    return (
        tables.complaints.group_by(month_of("opened_at"))
        .agg(*[(topic == t).sum().alias(t) for t in TOPICS])
        .join(confirmed, on="month")
        .with_columns(rates.round(2))
        .drop("confirmed")
        .sort("month")
    )
