from pathlib import Path

import joblib
import numpy as np
import polars as pl
import pytest
from polars.testing import assert_frame_equal

from platform_analytics.config import Settings
from platform_analytics.model import (
    ChurnModel,
    ModelQualityError,
    train,
)


def test_model_ranks_better_than_chance(
    model: ChurnModel,
    settings: Settings,
) -> None:
    """The held-out ROC AUC reaches the configured minimum."""
    assert model.auc >= settings.model.min_auc, (
        "the model should separate churners from loyal parents"
    )


def test_risk_is_a_probability(
    model: ChurnModel,
    current: pl.DataFrame,
) -> None:
    """Every risk is between 0 and 1, one per active parent."""
    risk = model.risk(current)
    assert risk["parent_id"].equals(current["parent_id"]), (
        "one risk per parent"
    )
    assert risk["risk"].is_between(0, 1).all(), (
        "risks should be probabilities"
    )


def test_model_round_trip(
    model: ChurnModel,
    current: pl.DataFrame,
    tmp_path: Path,
) -> None:
    """A saved and reloaded model gives the same risks."""
    path = tmp_path / "nested" / "model.joblib"
    model.save(path)
    assert_frame_equal(
        ChurnModel.load(path).risk(current),
        model.risk(current),
    )


def test_load_rejects_other_objects(tmp_path: Path) -> None:
    """Loading a file that holds something else raises TypeError."""
    path = tmp_path / "other.joblib"
    joblib.dump([], path)
    with pytest.raises(TypeError):
        ChurnModel.load(path)


def test_train_refuses_a_useless_model(
    labelled: tuple[pl.DataFrame, pl.Series],
    settings: Settings,
) -> None:
    """Training on shuffled labels fails the quality gate."""
    features, labels = labelled
    shuffled = pl.Series(
        np.random.default_rng(0).permutation(labels.to_numpy()),
    )
    with pytest.raises(ModelQualityError):
        train(features, shuffled, settings.model)


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
