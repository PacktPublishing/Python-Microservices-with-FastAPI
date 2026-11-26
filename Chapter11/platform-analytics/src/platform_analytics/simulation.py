from datetime import date

import numpy as np
import polars as pl
from loguru import logger

from .config import DataSettings
from .data import (
    SLOTS,
    STATUSES,
    TOPICS,
    Complaint,
    Parent,
    Reservation,
    Tables,
)

CITIES = ["Rome", "Milan", "Naples", "Turin"]
END = np.datetime64(date(2026, 10, 31), "D")
BASE_PRICE = {"morning": 30.0, "afternoon": 35.0, "night": 45.0}
MONDAY = np.datetime64("2024-01-01", "D")
DAYS = "timedelta64[D]"


def simulate(settings: DataSettings) -> Tables:
    """Simulate a year of parents, reservations and complaints.

    A hidden satisfaction per parent drives lifetime, ratings, cancellations and complaints.

    Args:
        settings (DataSettings):
            Number of parents, simulated days and random seed.

    Returns:
        Tables:
            The simulated tables.
    """
    rng = np.random.default_rng(settings.seed)
    n = settings.parents
    start = END - np.timedelta64(settings.days, "D")
    joined = rng.integers(0, settings.days, n)
    satisfaction = rng.normal(size=n)
    lifetime = rng.exponential(150 * np.exp(satisfaction))
    active_days = np.minimum(lifetime, settings.days - joined)
    signed_up = start + joined.astype(DAYS)
    parents = pl.DataFrame(
        {
            "parent_id": np.arange(1, n + 1),
            "signed_up": signed_up,
            "city": rng.choice(CITIES, n),
        },
        schema=Parent.dtypes,
    )
    weekly = rng.gamma(2.0, 0.6, n)
    counts = rng.poisson(weekly * active_days / 7)
    owner = np.repeat(np.arange(n), counts)
    offset = rng.uniform(size=owner.size) * active_days[owner]
    starts_at = signed_up[owner] + offset.astype(DAYS)
    weekend = (starts_at - MONDAY).astype(int) % 7 >= 4
    slot = np.where(
        weekend,
        rng.choice(SLOTS, owner.size, p=[0.2, 0.4, 0.4]),
        rng.choice(SLOTS, owner.size, p=[0.35, 0.5, 0.15]),
    )
    cancel = 1 / (1 + np.exp(2 + satisfaction[owner]))
    status = np.where(
        rng.random(owner.size) < cancel,
        "cancelled",
        rng.choice(STATUSES[:2], owner.size, p=[0.92, 0.08]),
    )
    base_price = np.vectorize(BASE_PRICE.__getitem__)(slot)
    price = base_price + rng.normal(0, 4, owner.size)
    noisy = 3.8 + 0.7 * satisfaction[owner]
    noisy = noisy + rng.normal(0, 0.6, owner.size)
    rated = (status == "confirmed") & (
        rng.random(owner.size) < 0.7
    )
    rating = np.where(
        rated,
        np.clip(np.round(noisy), 1, 5),
        np.nan,
    )
    reservations = (
        pl.DataFrame(
            {
                "parent_id": owner + 1,
                "starts_at": starts_at,
                "time_slot": slot,
                "status": status,
                "price": price.round(2),
                "rating": rating,
            },
            nan_to_null=True,
        )
        .sort("starts_at", maintain_order=True)
        .with_row_index("reservation_id", offset=1)
        .cast(Reservation.dtypes)
    )
    rate = 0.4 * np.exp(-satisfaction) * active_days / 90
    complaint_counts = rng.poisson(rate)
    who = np.repeat(np.arange(n), complaint_counts)
    when = rng.uniform(size=who.size) * active_days[who]
    complaints = (
        pl.DataFrame(
            {
                "parent_id": who + 1,
                "opened_at": signed_up[who] + when.astype(DAYS),
                "topic": rng.choice(TOPICS, who.size),
            },
        )
        .sort("opened_at", maintain_order=True)
        .with_row_index("complaint_id", offset=1)
        .cast(Complaint.dtypes)
    )
    logger.info(
        "Simulated {} parents, {} reservations, {} complaints",
        n,
        len(reservations),
        len(complaints),
    )
    return Tables(
        parents=Parent.DataFrame(parents),
        reservations=Reservation.DataFrame(reservations),
        complaints=Complaint.DataFrame(complaints),
    )
