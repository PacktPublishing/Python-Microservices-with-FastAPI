import typing as ty
from pathlib import Path

import joblib
import polars as pl
from loguru import logger
from pydantic import BaseModel
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from .config import ModelSettings
from .data import FROZEN
from .features import FEATURES


class ModelQualityError(RuntimeError):
    """The trained model ranks parents too poorly to be served."""


class ChurnModel(BaseModel):
    """A fitted churn pipeline with its score and training data."""

    model_config = FROZEN
    pipeline: Pipeline
    auc: float
    reference: pl.DataFrame

    def risk(self, features: pl.DataFrame) -> pl.DataFrame:
        """Estimate the probability that each parent churns.

        Args:
            features (pl.DataFrame):
                One row per parent, as built by `parent_features`.

        Returns:
            pl.DataFrame:
                Each parent's identifier and churn probability.
        """
        probability = self.pipeline.predict_proba(
            features.select(FEATURES),
        )[:, 1]
        return features.select("parent_id").with_columns(
            risk=pl.Series(probability),
        )

    def save(self, path: Path) -> None:
        """Write the model to `path`.

        Args:
            path (Path):
                Destination file, its folder created when missing.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info("Saved churn model to {}", path)

    @classmethod
    def load(cls, path: Path) -> ty.Self:
        """Read a model written by `save`.

        Args:
            path (Path):
                File written by `save`.

        Returns:
            ChurnModel:
                The model.

        Raises:
            TypeError:
                If the file does not contain a `ChurnModel`.
        """
        model = joblib.load(path)
        if not isinstance(model, cls):
            raise TypeError(f"{path} is not a churn model")
        return model


def train(
    features: pl.DataFrame,
    labels: pl.Series,
    settings: ModelSettings,
) -> ChurnModel:
    """Fit a churn model and check it on held-out parents.

    Args:
        features (pl.DataFrame):
            One row per parent.

        labels (pl.Series):
            Whether each parent churned.

        settings (ModelSettings):
            Test share and minimum accepted ROC AUC.

    Returns:
        ChurnModel:
            The fitted model.

    Raises:
        ModelQualityError:
            If the held-out ROC AUC is below `settings.min_auc`.
    """
    x_train, x_test, y_train, y_test = train_test_split(
        features.select(FEATURES),
        labels,
        test_size=settings.test_size,
        stratify=labels,
        random_state=0,
    )
    pipeline = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(class_weight="balanced"),
    )
    pipeline.fit(x_train, y_train)
    scores = pipeline.predict_proba(x_test)[:, 1]
    auc = float(roc_auc_score(y_test, scores))
    logger.info("Churn model ROC AUC: {:.3f}", auc)
    if auc < settings.min_auc:
        raise ModelQualityError(
            f"ROC AUC {auc:.3f} is below {settings.min_auc}",
        )
    return ChurnModel(
        pipeline=pipeline,
        auc=auc,
        reference=x_train,
    )
