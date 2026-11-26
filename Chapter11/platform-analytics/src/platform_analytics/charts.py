from io import BytesIO

import numpy as np
import polars as pl
from matplotlib.figure import Figure

FIVE_DAYS = np.timedelta64(5, "D")


def weekly_chart(weekly: pl.DataFrame) -> bytes:
    """Draw weekly reservations and revenue as a PNG image.

    Args:
        weekly (pl.DataFrame):
            The output of `weekly_activity`.

    Returns:
        bytes:
            The PNG image.
    """
    figure = Figure(figsize=(8, 4), layout="constrained")
    count, revenue = figure.subplots(2, 1, sharex=True)
    week = weekly["week"].to_numpy()
    count.plot(week, weekly["reservations"].to_numpy())
    count.set_ylabel("Reservations")
    revenue.bar(
        week,
        weekly["revenue"].to_numpy(),
        width=FIVE_DAYS,
    )
    revenue.set_ylabel("Revenue (EUR)")
    figure.suptitle("Weekly activity")
    buffer = BytesIO()
    figure.savefig(buffer, format="png")
    return buffer.getvalue()
