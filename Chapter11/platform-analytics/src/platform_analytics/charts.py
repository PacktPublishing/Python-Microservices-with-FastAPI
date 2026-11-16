from io import BytesIO

import pandas as pd
from matplotlib.figure import Figure


def weekly_chart(weekly: pd.DataFrame) -> bytes:
    """Draw weekly reservations and revenue as a PNG image.

    Args:
        weekly (pd.DataFrame):
            The output of `weekly_activity`.

    Returns:
        bytes:
            The PNG image.
    """
    figure = Figure(figsize=(8, 4), layout="constrained")
    count, revenue = figure.subplots(2, 1, sharex=True)
    count.plot(weekly.index, weekly["reservations"])
    count.set_ylabel("Reservations")
    revenue.bar(weekly.index, weekly["revenue"], width=5)
    revenue.set_ylabel("Revenue (EUR)")
    figure.suptitle("Weekly activity")
    buffer = BytesIO()
    figure.savefig(buffer, format="png")
    return buffer.getvalue()
