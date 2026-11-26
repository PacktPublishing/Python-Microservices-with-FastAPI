import typing as ty
from collections.abc import Callable
from pathlib import Path

import polars as pl
import pytest
from pydantic import ValidationError

from platform_analytics.config import QualitySettings
from platform_analytics.data import Tables
from platform_analytics.model import ChurnModel
from platform_analytics.quality import check_drift, psi


def first_row(column: str, value: ty.Any) -> pl.Expr:
    """Replace the value of `column` in the first row only.

    Args:
        column (str):
            The column to change.

        value (ty.Any):
            The new value of the first row.

    Returns:
        pl.Expr:
            The changed column.
    """
    first = pl.int_range(pl.len()) == 0
    return (
        pl.when(first)
        .then(pl.lit(value))
        .otherwise(pl.col(column))
        .alias(column)
    )


def null_parents(frame: pl.DataFrame) -> pl.DataFrame:
    """Remove the parent of one reservation."""
    return frame.with_columns(first_row("parent_id", None))


def duplicate_ids(frame: pl.DataFrame) -> pl.DataFrame:
    """Give every reservation the same identifier."""
    return frame.with_columns(pl.lit(1).alias("reservation_id"))


def free_reservation(frame: pl.DataFrame) -> pl.DataFrame:
    """Make one reservation cost nothing."""
    return frame.with_columns(first_row("price", 0.0))


def out_of_scale_rating(frame: pl.DataFrame) -> pl.DataFrame:
    """Rate one reservation out of ten instead of five."""
    return frame.with_columns(first_row("rating", 9.0))


@pytest.mark.parametrize(
    ("corrupt", "column"),
    [
        (null_parents, "parent_id"),
        (duplicate_ids, "reservation_id"),
        (free_reservation, "price"),
        (out_of_scale_rating, "rating"),
    ],
)
def test_corrupted_reservations_are_refused(
    tables: Tables,
    corrupt: Callable[[pl.DataFrame], pl.DataFrame],
    column: str,
) -> None:
    """Each kind of corruption is refused, naming the broken column."""
    with pytest.raises(ValidationError, match=column):
        Tables(
            parents=tables.parents,
            reservations=corrupt(tables.reservations),
            complaints=tables.complaints,
        )


@pytest.mark.parametrize(
    ("column", "value"),
    [("status", "lost"), ("time_slot", "lunch")],
)
def test_unknown_values_are_refused_when_read(
    tables: Tables,
    tmp_path: Path,
    column: str,
    value: str,
) -> None:
    """A CSV value outside a `Literal` cannot even be read."""
    tables.save(tmp_path)
    path = tmp_path / "reservations.csv"
    raw = pl.read_csv(path).with_columns(first_row(column, value))
    raw.write_csv(path)
    with pytest.raises(pl.exceptions.PolarsError, match=value):
        Tables.load(tmp_path)


def test_psi_of_identical_samples_is_zero(
    current: pl.DataFrame,
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
    shifted = model.reference.with_columns(
        pl.col("tenure_days") + shift,
    )
    report = check_drift(model.reference, shifted, quality)
    assert len(report.problems) == 1, "only one feature moved"
    assert "tenure_days" in report.problems[0], (
        "the problem should name the drifted feature"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
