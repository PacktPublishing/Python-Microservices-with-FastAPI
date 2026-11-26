from ipaddress import ip_address
from pathlib import Path

from pydantic import Field, IPvAnyAddress
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "ANALYTICS_"
COMMON_CONFIG: SettingsConfigDict = {
    "env_file": ".env",
    "extra": "ignore",
    "validate_default": True,
}


class DataSettings(BaseSettings):
    """Where the platform's tables live and how to simulate them."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "DATA_",
        **COMMON_CONFIG,
    )
    folder: Path = Field(
        Path("data"),
        description="Folder holding the platform's tables.",
    )
    parents: int = Field(
        2000,
        description="Parents to simulate.",
        gt=0,
    )
    days: int = Field(
        365,
        description="Days of activity to simulate.",
        ge=120,
    )
    seed: int = Field(
        11,
        description="Seed of the random simulation.",
    )


class ModelSettings(BaseSettings):
    """Where the churn model lives and how it is trained."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "MODEL_",
        **COMMON_CONFIG,
    )
    path: Path = Field(
        Path("models/churn.joblib"),
        description="File holding the churn model.",
    )
    horizon_days: int = Field(
        30,
        description="Days without booking that mean churn.",
        gt=0,
    )
    test_size: float = Field(
        0.25,
        description="Share of parents held out for testing.",
        gt=0,
        lt=1,
    )
    min_auc: float = Field(
        0.7,
        description="Lowest ROC AUC a model may have.",
        ge=0.5,
        le=1,
    )


class QualitySettings(BaseSettings):
    """Thresholds that decide whether the data can be trusted."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "QUALITY_",
        **COMMON_CONFIG,
    )
    max_drift: float = Field(
        0.2,
        description="Largest PSI of a feature.",
        gt=0,
    )


class ServerSettings(BaseSettings):
    """Address the analytics API listens on."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "SERVER_",
        **COMMON_CONFIG,
    )
    host: IPvAnyAddress = Field(
        ip_address("127.0.0.1"),
        description="Address the API listens on.",
    )
    port: int = Field(
        8011,
        description="Port the API listens on.",
        ge=1,
        le=65535,
    )


class Settings(BaseSettings):
    """All the settings of the analytics service."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        **COMMON_CONFIG,
    )
    data: DataSettings = Field(default_factory=DataSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    quality: QualitySettings = Field(
        default_factory=QualitySettings,
    )
    server: ServerSettings = Field(
        default_factory=ServerSettings,
    )
