import numpy as np
import polars as pl
from loguru import logger
from pydantic import BaseModel, computed_field

from .config import QualitySettings
from .features import FEATURES


class QualityReport(BaseModel):
    """The problems one check found; none means the check passed."""

    check: str
    problems: list[str] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ok(self) -> bool:
        """Whether the check found no problem."""
        return not self.problems


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
    reference: pl.DataFrame,
    current: pl.DataFrame,
    settings: QualitySettings,
) -> QualityReport:
    """Compare today's features with the model's training data.

    Args:
        reference (pl.DataFrame):
            The features the model was trained on.

        current (pl.DataFrame):
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
            reference[column].drop_nulls().to_numpy(),
            current[column].drop_nulls().to_numpy(),
        )
        logger.debug("PSI of {}: {:.3f}", column, score)
        if score > settings.max_drift:
            problems.append(
                f"{column} drifted (PSI {score:.2f})",
            )
    return QualityReport(check="drift", problems=problems)
