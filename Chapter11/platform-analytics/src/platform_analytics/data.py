import typing as ty
from datetime import date
from pathlib import Path

import patito as pt
import polars as pl
from loguru import logger
from pydantic import AfterValidator, BaseModel, ConfigDict

Status = ty.Literal["confirmed", "refused", "cancelled"]
Slot = ty.Literal["morning", "afternoon", "night"]
Topic = ty.Literal["payments", "cancellation", "sitter", "app"]
STATUSES = ty.get_args(Status)
SLOTS = ty.get_args(Slot)
TOPICS = ty.get_args(Topic)
FROZEN = ConfigDict(frozen=True, arbitrary_types_allowed=True)


class Parent(pt.Model):
    """A parent who signed up, when, and in which city."""

    parent_id: int = pt.Field(unique=True)
    signed_up: date
    city: str


class Reservation(pt.Model):
    """A booking, with its day, slot, status, price and rating."""

    reservation_id: int = pt.Field(unique=True)
    parent_id: int
    starts_at: date
    time_slot: Slot
    status: Status
    price: float = pt.Field(gt=0)
    rating: float | None = pt.Field(ge=1, le=5)


class Complaint(pt.Model):
    """A complaint opened with support, with its day and topic."""

    complaint_id: int = pt.Field(unique=True)
    parent_id: int
    opened_at: date
    topic: Topic


def enforce(model: type[pt.Model]) -> AfterValidator:
    """Build a Pydantic validator that checks a table against `model`.

    Args:
        model (type[pt.Model]):
            The contract every row of the table must follow.

    Returns:
        AfterValidator:
            Returns the table unchanged, or raises a `ValueError` that lists every broken rule.
    """

    def validate(frame: pl.DataFrame) -> pl.DataFrame:
        """Check the columns, types and rules of `frame`.

        Args:
            frame (pl.DataFrame):
                The table to validate.

        Returns:
            pl.DataFrame:
                The same table, now known to be valid.
        """
        model.validate(frame)
        return frame

    return AfterValidator(validate)


class Tables(BaseModel):
    """The three tables the analytics portal reads, validated."""

    model_config = FROZEN
    parents: ty.Annotated[pl.DataFrame, enforce(Parent)]
    reservations: ty.Annotated[
        pl.DataFrame,
        enforce(Reservation),
    ]
    complaints: ty.Annotated[pl.DataFrame, enforce(Complaint)]

    def save(self, folder: Path) -> None:
        """Write every table as a CSV file in `folder`.

        Args:
            folder (Path):
                Destination folder, created when missing.
        """
        folder.mkdir(parents=True, exist_ok=True)
        for table, name in (
            (self.parents, "parents"),
            (self.reservations, "reservations"),
            (self.complaints, "complaints"),
        ):
            self._save(table, folder / f"{name}.csv")

    @staticmethod
    def _save(table: pl.DataFrame, path: Path) -> None:
        """Write one table as a CSV file.

        Args:
            table (pl.DataFrame):
                The table to write.

            path (Path):
                Destination file.
        """
        table.write_csv(path)
        logger.debug("Saved {} rows to {}", len(table), path)

    @classmethod
    def load(cls, folder: Path) -> ty.Self:
        """Read the tables written by `save`, with their declared types.

        Args:
            folder (Path):
                Folder that contains the three CSV files.

        Returns:
            Tables:
                The validated tables.
        """
        return cls(
            parents=cls._load(folder / "parents.csv", Parent),
            reservations=cls._load(
                folder / "reservations.csv",
                Reservation,
            ),
            complaints=cls._load(
                folder / "complaints.csv",
                Complaint,
            ),
        )

    @staticmethod
    def _load(path: Path, model: type[pt.Model]) -> pl.DataFrame:
        """Read one CSV file with the column types of `model`.

        Args:
            path (Path):
                The CSV file to read.

            model (type[pt.Model]):
                The model that declares the type of each column.

        Returns:
            pl.DataFrame:
                The table, typed as the model declares.
        """
        return pl.read_csv(path, schema_overrides=model.dtypes)
