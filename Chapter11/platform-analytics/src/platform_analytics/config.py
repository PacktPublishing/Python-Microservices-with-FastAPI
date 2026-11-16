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
    folder: Path = Path("data")
    parents: int = Field(2000, gt=0)
    days: int = Field(365, ge=120)
    seed: int = 11


class ModelSettings(BaseSettings):
    """Where the churn model lives and how it is trained."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "MODEL_",
        **COMMON_CONFIG,
    )
    path: Path = Path("models/churn.joblib")
    horizon_days: int = Field(30, gt=0)
    test_size: float = Field(0.25, gt=0, lt=1)
    min_auc: float = Field(0.7, ge=0.5, le=1)


class QualitySettings(BaseSettings):
    """Thresholds that decide whether the data can be trusted."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "QUALITY_",
        **COMMON_CONFIG,
    )
    max_null_rate: float = Field(0.05, ge=0, le=1)
    max_drift: float = Field(0.2, gt=0)


class ServerSettings(BaseSettings):
    """Address the analytics API listens on."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "SERVER_",
        **COMMON_CONFIG,
    )
    host: IPvAnyAddress = ip_address("127.0.0.1")
    port: int = Field(8011, ge=1, le=65535)


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
