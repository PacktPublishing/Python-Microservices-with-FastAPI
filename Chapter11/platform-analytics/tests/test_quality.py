from collections.abc import Callable

import numpy as np
import pandas as pd
import pytest

from platform_analytics.config import QualitySettings
from platform_analytics.data import Tables
from platform_analytics.model import ChurnModel
from platform_analytics.quality import (
    check_drift,
    check_reservations,
    psi,
)


def null_parents(frame: pd.DataFrame) -> None:
    """Remove the parent of every reservation."""
    frame["parent_id"] = np.nan


def duplicate_ids(frame: pd.DataFrame) -> None:
    """Give every reservation the same identifier."""
    frame["reservation_id"] = 1


def unknown_status(frame: pd.DataFrame) -> None:
    """Use a status the platform does not know."""
    frame.loc[0, "status"] = "lost"


def unknown_slot(frame: pd.DataFrame) -> None:
    """Use a time slot the platform does not know."""
    frame.loc[0, "time_slot"] = "lunch"


def free_reservation(frame: pd.DataFrame) -> None:
    """Make one reservation cost nothing."""
    frame.loc[0, "price"] = 0.0


def out_of_scale_rating(frame: pd.DataFrame) -> None:
    """Rate one reservation out of ten instead of five."""
    frame.loc[0, "rating"] = 9.0


def test_clean_reservations_pass(
    tables: Tables,
    quality: QualitySettings,
) -> None:
    """The simulated reservations satisfy every rule."""
    report = check_reservations(tables.reservations, quality)
    assert report.ok, f"unexpected problems: {report.problems}"


@pytest.mark.parametrize(
    "corrupt",
    [
        null_parents,
        duplicate_ids,
        unknown_status,
        unknown_slot,
        free_reservation,
        out_of_scale_rating,
    ],
)
def test_corrupted_reservations_fail(
    tables: Tables,
    quality: QualitySettings,
    corrupt: Callable[[pd.DataFrame], None],
) -> None:
    """Each kind of corruption produces exactly one problem."""
    frame = tables.reservations.copy()
    corrupt(frame)
    report = check_reservations(frame, quality)
    assert len(report.problems) == 1, (
        f"{corrupt.__name__} should break one rule, got "
        f"{report.problems}"
    )


def test_psi_of_identical_samples_is_zero(
    current: pd.DataFrame,
) -> None:
    """A sample compared with itself has not drifted."""
    values = current["tenure_days"].to_numpy()
    assert psi(values, values) == pytest.approx(0), (
        "identical samples should have zero PSI"
    )


def test_unchanged_features_do_not_drift(
    model: ChurnModel,
    quality: QualitySettings,
) -> None:
    """The training data compared with itself reports no drift."""
    report = check_drift(
        model.reference,
        model.reference,
        quality,
    )
    assert report.ok, f"unexpected drift: {report.problems}"


def test_shifted_feature_drifts(
    model: ChurnModel,
    quality: QualitySettings,
    shift: float,
) -> None:
    """Moving one feature far away is reported for that feature only."""
    shifted = model.reference.assign(
        tenure_days=model.reference["tenure_days"] + shift,
    )
    report = check_drift(model.reference, shifted, quality)
    assert len(report.problems) == 1, "only one feature moved"
    assert "tenure_days" in report.problems[0], (
        "the problem should name the drifted feature"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
