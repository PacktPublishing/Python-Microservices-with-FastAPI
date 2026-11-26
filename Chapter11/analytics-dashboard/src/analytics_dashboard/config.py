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
    api_url: HttpUrl = HttpUrl("http://127.0.0.1:8011")
    timeout: float = Field(10.0, gt=0)
    host: IPvAnyAddress = ip_address("127.0.0.1")
    port: int = Field(8012, ge=1, le=65535)
    limit: int = Field(10, ge=1, le=100)
