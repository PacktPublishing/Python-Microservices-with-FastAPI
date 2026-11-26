import numpy as np
import pandas as pd
from loguru import logger

from .config import DataSettings
from .data import SLOTS, STATUSES, Tables

CITIES = ["Rome", "Milan", "Naples", "Turin"]
TOPICS = ["payments", "cancellation", "sitter", "app"]
END = pd.Timestamp("2026-10-31")


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
    start = END - pd.Timedelta(settings.days, unit="D")
    joined = rng.integers(0, settings.days, n)
    satisfaction = rng.normal(size=n)
    lifetime = rng.exponential(150 * np.exp(satisfaction))
    active_days = np.minimum(lifetime, settings.days - joined)
    parents = pd.DataFrame(
        {
            "parent_id": np.arange(1, n + 1),
            "signed_up": start + pd.to_timedelta(joined, "D"),
            "city": rng.choice(CITIES, n),
        },
    )
    weekly = rng.gamma(2.0, 0.6, n)
    counts = rng.poisson(weekly * active_days / 7)
    owner = np.repeat(np.arange(n), counts)
    offset = rng.uniform(size=owner.size) * active_days[owner]
    starts_at = parents["signed_up"].to_numpy()[owner]
    starts_at = starts_at + pd.to_timedelta(offset, "D")
    weekend = np.asarray(starts_at.day_of_week >= 4)
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
    base_price = pd.Series(slot).map(
        {"morning": 30.0, "afternoon": 35.0, "night": 45.0},
    )
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
    reservations = pd.DataFrame(
        {
            "parent_id": owner + 1,
            "starts_at": starts_at.floor("D"),
            "time_slot": slot,
            "status": status,
            "price": price.round(2),
            "rating": rating,
        },
    ).sort_values("starts_at", ignore_index=True)
    reservations.insert(
        0,
        "reservation_id",
        np.arange(1, len(reservations) + 1),
    )
    rate = 0.4 * np.exp(-satisfaction) * active_days / 90
    complaint_counts = rng.poisson(rate)
    who = np.repeat(np.arange(n), complaint_counts)
    when = rng.uniform(size=who.size) * active_days[who]
    opened_at = parents["signed_up"].to_numpy()[who]
    complaints = pd.DataFrame(
        {
            "parent_id": who + 1,
            "opened_at": (
                opened_at + pd.to_timedelta(when, "D")
            ).floor("min"),
            "topic": rng.choice(TOPICS, who.size),
        },
    ).sort_values("opened_at", ignore_index=True)
    complaints.insert(
        0,
        "complaint_id",
        np.arange(1, len(complaints) + 1),
    )
    logger.info(
        "Simulated {} parents, {} reservations, {} complaints",
        n,
        len(reservations),
        len(complaints),
    )
    return Tables(parents, reservations, complaints)
