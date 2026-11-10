from ipaddress import ip_address

from pydantic import Field, HttpUrl, IPvAnyAddress, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "SUPPORT_MCP_"
COMMON_CONFIG: SettingsConfigDict = {
    "env_file": ".env",
    "extra": "ignore",
    "validate_default": True,
}


class SupportSettings(BaseSettings):
    """Where the customer support service of Chapter 9 runs."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "SUPPORT_", **COMMON_CONFIG
    )
    url: HttpUrl = HttpUrl("http://127.0.0.1:8009")
    timeout: float = Field(60.0, gt=0)


class ServerSettings(BaseSettings):
    """Where the MCP server listens when served over HTTP."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "SERVER_", **COMMON_CONFIG
    )
    host: IPvAnyAddress = ip_address("127.0.0.1")
    port: int = Field(8010, ge=1, le=65535)


class Settings(BaseSettings):
    """Settings shared by every way of running the server."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX, **COMMON_CONFIG
    )
    support: SupportSettings = Field(
        default_factory=SupportSettings
    )
    server: ServerSettings = Field(
        default_factory=ServerSettings,
    )


class AuthSettings(BaseSettings):
    """Secret shared with the authenticator service of Chapter 8."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "AUTH_", **COMMON_CONFIG
    )
    jwt_secret_key: SecretStr = Field(min_length=32)
    token_minutes: int = Field(30, ge=1)
