from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl
import pytest
from fastapi.testclient import TestClient

from platform_analytics.api import create_app
from platform_analytics.config import (
    DataSettings,
    ModelSettings,
    QualitySettings,
    Settings,
)
from platform_analytics.data import Tables
from platform_analytics.features import (
    latest_day,
    parent_features,
    training_set,
)
from platform_analytics.model import ChurnModel, train
from platform_analytics.simulation import simulate


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Settings that keep data and model in a temporary folder."""
    return Settings(
        data=DataSettings(folder=tmp_path / "data", parents=400),
        model=ModelSettings(path=tmp_path / "model.joblib"),
    )


@pytest.fixture
def env(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> Settings:
    """Expose `settings` through environment variables."""
    monkeypatch.setenv(
        "ANALYTICS_DATA_FOLDER",
        str(settings.data.folder),
    )
    monkeypatch.setenv(
        "ANALYTICS_DATA_PARENTS",
        str(settings.data.parents),
    )
    monkeypatch.setenv(
        "ANALYTICS_MODEL_PATH",
        str(settings.model.path),
    )
    return settings


@pytest.fixture
def quality() -> QualitySettings:
    """Default data quality thresholds."""
    return QualitySettings()


@pytest.fixture
def tables(settings: Settings) -> Tables:
    """A small simulated platform."""
    return simulate(settings.data)


@pytest.fixture
def horizon(settings: Settings) -> int:
    """Days without reservations that count as churn."""
    return settings.model.horizon_days


@pytest.fixture
def labelled(
    tables: Tables,
    horizon: int,
) -> tuple[pl.DataFrame, pl.Series]:
    """Features and churn labels of the simulated platform."""
    return training_set(tables, horizon)


@pytest.fixture
def model(
    labelled: tuple[pl.DataFrame, pl.Series],
    settings: Settings,
) -> ChurnModel:
    """A churn model trained on the simulated platform."""
    features, labels = labelled
    return train(features, labels, settings.model)


@pytest.fixture
def current(tables: Tables) -> pl.DataFrame:
    """Features of the parents active on the last day."""
    return parent_features(tables, latest_day(tables))


@pytest.fixture
def saved(
    tables: Tables,
    model: ChurnModel,
    settings: Settings,
) -> Settings:
    """Settings whose data folder and model file exist."""
    tables.save(settings.data.folder)
    model.save(settings.model.path)
    return settings


@pytest.fixture
def client(saved: Settings) -> Iterator[TestClient]:
    """A client of the analytics API, started on the saved data."""
    with TestClient(create_app(saved)) as client:
        yield client


@pytest.fixture
def run_server() -> Iterator[MagicMock]:
    """Replace `uvicorn.run` so the serve command returns."""
    with patch("platform_analytics.__main__.uvicorn.run") as run:
        yield run


@pytest.fixture
def png_signature() -> bytes:
    """The first bytes of every PNG file."""
    return b"\x89PNG"


@pytest.fixture
def limit() -> int:
    """Number of at-risk parents to request."""
    return 3


@pytest.fixture
def unknown_parent() -> int:
    """A parent identifier that never exists."""
    return 0


@pytest.fixture
def shift() -> float:
    """An offset large enough to move a whole distribution."""
    return 1000.0


@pytest.fixture
def week_days() -> list[str]:
    """The days of the week, in calendar order from Monday."""
    return [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
