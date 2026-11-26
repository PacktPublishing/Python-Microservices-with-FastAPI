import subprocess
import sys
from unittest.mock import MagicMock

import polars as pl
import pytest

from platform_analytics.__main__ import main
from platform_analytics.config import Settings
from platform_analytics.data import Tables


def test_simulate_then_train(env: Settings) -> None:
    """The commands write the tables, then the model."""
    main(["simulate"])
    main(["train"])
    assert (env.data.folder / "reservations.csv").exists(), (
        "simulate should save the reservations"
    )
    assert env.model.path.exists(), "train should save the model"


def test_train_refuses_bad_data(
    env: Settings,
    tables: Tables,
) -> None:
    """Training stops when the reservations break their contract."""
    broken = tables.model_copy(
        update={
            "reservations": tables.reservations.with_columns(
                -pl.col("price"),
            ),
        },
    )
    broken.save(env.data.folder)
    with pytest.raises(SystemExit):
        main(["train"])
    assert not env.model.path.exists(), "no model should be saved"


def test_serve(env: Settings, run_server: MagicMock) -> None:
    """Serve starts uvicorn on the configured port."""
    main(["serve"])
    assert run_server.call_args.kwargs["port"] == env.server.port


@pytest.mark.integration
def test_command_line_end_to_end(env: Settings) -> None:
    """The module runs as a program and trains a model."""
    for command in ("simulate", "train"):
        subprocess.run(
            [sys.executable, "-m", "platform_analytics", command],
            check=True,
        )
    assert env.model.path.exists(), "the model should be saved"


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
