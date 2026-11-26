import polars as pl
import uvicorn
from loguru import logger
from pydantic import ValidationError
from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliSubCommand,
    SettingsConfigDict,
)

from .api import create_app
from .config import Settings
from .data import Tables
from .features import training_set
from .model import train
from .simulation import simulate


class Simulate(Settings):
    """Simulate a year of platform data and save it."""

    def cli_cmd(self) -> None:
        """Write the simulated tables to the data folder."""
        simulate(self.data).save(self.data.folder)


class Train(Settings):
    """Train the churn model on the saved data."""

    def cli_cmd(self) -> None:
        """Refuse bad data, then train, check and save the model."""
        try:
            tables = Tables.load(self.data.folder)
        except (
            ValidationError,
            pl.exceptions.PolarsError,
        ) as error:
            raise SystemExit(
                f"Refusing to train: {error}",
            ) from error
        features, labels = training_set(
            tables,
            self.model.horizon_days,
        )
        train(features, labels, self.model).save(self.model.path)


class Serve(Settings):
    """Serve the analytics API."""

    def cli_cmd(self) -> None:
        """Serve until interrupted."""
        logger.info("Serving on port {}", self.server.port)
        uvicorn.run(
            create_app(self),
            host=str(self.server.host),
            port=self.server.port,
        )


class Runner(BaseSettings):
    """Command-line entry point of the analytics service."""

    model_config = SettingsConfigDict(
        cli_kebab_case=True,
        cli_enforce_required=True,
    )

    simulate: CliSubCommand[Simulate]
    train: CliSubCommand[Train]
    serve: CliSubCommand[Serve]

    def cli_cmd(self) -> None:
        """Dispatch to the selected subcommand."""
        CliApp.run_subcommand(self)


def main(args: list[str] | None = None) -> None:
    """Parse the command line, or `args` when given, and run it.

    Run it with `python -m platform_analytics <subcommand>`.

    Args:
        args (list[str] | None):
            Arguments to parse instead of the command line.
    """
    CliApp.run(Runner, cli_args=args)


if __name__ == "__main__":
    main()
