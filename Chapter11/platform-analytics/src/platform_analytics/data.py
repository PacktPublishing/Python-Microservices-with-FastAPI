from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from loguru import logger

STATUSES = ["confirmed", "refused", "cancelled"]
SLOTS = ["morning", "afternoon", "night"]


@dataclass(frozen=True)
class Tables:
    """The three tables the analytics portal reads."""

    parents: pd.DataFrame
    reservations: pd.DataFrame
    complaints: pd.DataFrame

    def save(self, folder: Path) -> None:
        """Write every table as a CSV file in `folder`.

        Args:
            folder (Path):
                Destination folder, created when missing.
        """
        folder.mkdir(parents=True, exist_ok=True)
        for name in ("parents", "reservations", "complaints"):
            table: pd.DataFrame = getattr(self, name)
            table.to_csv(folder / f"{name}.csv", index=False)
            logger.debug("Saved {} rows of {}", len(table), name)

    @classmethod
    def load(cls, folder: Path) -> "Tables":
        """Read the tables written by `save`.

        Args:
            folder (Path):
                Folder that contains the three CSV files.

        Returns:
            Tables:
                The tables, with dates parsed.
        """
        return cls(
            parents=pd.read_csv(
                folder / "parents.csv",
                parse_dates=["signed_up"],
            ),
            reservations=pd.read_csv(
                folder / "reservations.csv",
                parse_dates=["starts_at"],
            ),
            complaints=pd.read_csv(
                folder / "complaints.csv",
                parse_dates=["opened_at"],
            ),
        )
