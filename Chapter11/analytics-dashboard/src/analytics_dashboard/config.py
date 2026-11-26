from ipaddress import ip_address

from pydantic import Field, HttpUrl, IPvAnyAddress
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Where the analytics API lives and where the dashboard listens."""

    model_config = SettingsConfigDict(
        env_prefix="DASHBOARD_",
        env_file=".env",
        extra="ignore",
    )
    api_url: HttpUrl = Field(
        HttpUrl("http://127.0.0.1:8011"),
        description="Base URL of the analytics API.",
    )
    timeout: float = Field(
        10.0,
        description="Seconds to wait for the API.",
        gt=0,
    )
    host: IPvAnyAddress = Field(
        ip_address("127.0.0.1"),
        description="Address the dashboard listens on.",
    )
    port: int = Field(
        8012,
        description="Port the dashboard listens on.",
        ge=1,
        le=65535,
    )
    limit: int = Field(
        10,
        description="At-risk parents shown at first.",
        ge=1,
        le=100,
    )
