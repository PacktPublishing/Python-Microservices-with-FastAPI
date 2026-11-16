import numpy as np
import pandas as pd
from loguru import logger
from pydantic import BaseModel, computed_field

from .config import QualitySettings
from .data import SLOTS, STATUSES
from .features import FEATURES

REQUIRED = ["reservation_id", "parent_id", "starts_at", "status"]


class QualityReport(BaseModel):
    """The problems one check found; none means the check passed."""

    check: str
    problems: list[str] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ok(self) -> bool:
        """Whether the check found no problem."""
        return not self.problems


def check_reservations(
    reservations: pd.DataFrame,
    settings: QualitySettings,
) -> QualityReport:
    """Check the reservations table against its contract.

    Args:
        reservations (pd.DataFrame):
            The reservations table.

        settings (QualitySettings):
            Maximum share of nulls in a required column.

    Returns:
        QualityReport:
            Every violated rule, as a readable message.
    """
    problems = []
    null_rates = reservations[REQUIRED].isna().mean()
    for column, rate in null_rates.items():
        if rate > settings.max_null_rate:
            problems.append(f"{column} is {rate:.0%} null")
    if reservations["reservation_id"].duplicated().any():
        problems.append("reservation_id has duplicates")
    if not reservations["status"].dropna().isin(STATUSES).all():
        problems.append("status has unknown values")
    if not reservations["time_slot"].isin(SLOTS).all():
        problems.append("time_slot has unknown values")
    if (reservations["price"] <= 0).any():
        problems.append("price is not always positive")
    ratings = reservations["rating"].dropna()
    if not ratings.between(1, 5).all():
        problems.append("rating is outside 1 to 5")
    for problem in problems:
        logger.warning("Reservations: {}", problem)
    return QualityReport(check="reservations", problems=problems)


def psi(reference: np.ndarray, current: np.ndarray) -> float:
    """Compute the population stability index of two samples.

    The bins are the deciles of `reference`; zero means the two samples are spread in the same way.

    Args:
        reference (np.ndarray):
            Values seen when the model was trained.

        current (np.ndarray):
            Values seen now.

    Returns:
        float:
            The index, larger when the distributions differ more.
    """
    deciles = np.quantile(reference, np.linspace(0.1, 0.9, 9))
    inner = np.unique(deciles)
    edges = np.concatenate(([-np.inf], inner, [np.inf]))
    expected = np.histogram(reference, edges)[0] / reference.size
    actual = np.histogram(current, edges)[0] / current.size
    expected = np.clip(expected, 1e-4, None)
    actual = np.clip(actual, 1e-4, None)
    ratio = np.log(actual / expected)
    return float(np.sum((actual - expected) * ratio))


def check_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    settings: QualitySettings,
) -> QualityReport:
    """Compare today's features with the model's training data.

    Args:
        reference (pd.DataFrame):
            The features the model was trained on.

        current (pd.DataFrame):
            The features the model scores now.

        settings (QualitySettings):
            Largest population stability index accepted.

    Returns:
        QualityReport:
            One problem per feature that drifted.
    """
    problems = []
    for column in FEATURES:
        score = psi(
            reference[column].dropna().to_numpy(),
            current[column].dropna().to_numpy(),
        )
        logger.debug("PSI of {}: {:.3f}", column, score)
        if score > settings.max_drift:
            problems.append(
                f"{column} drifted (PSI {score:.2f})",
            )
    return QualityReport(check="drift", problems=problems)
