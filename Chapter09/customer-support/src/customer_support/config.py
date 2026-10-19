__all__ = ["Settings"]


from pydantic import Field, IPvAnyAddress
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "CUSTOMER_SUPPORT_"
COMMON_CONFIG = {
    "case_sensitive": False,
    "env_file_encoding": "utf-8",
    "env_file": ".env",
    "extra": "ignore",
    "validate_assignment": True,
    "validate_default": True,
}


class APISettings(BaseSettings):
    """API settings."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "API_",
        **COMMON_CONFIG,
    )

    host: IPvAnyAddress = Field(
        "127.0.0.1",
        description="Webservice bind host.",
    )
    port: int = Field(
        8009,
        description="Webservice port.",
        ge=1,
        le=65535,
    )


class LLMSettings(BaseSettings):
    """LLM settings."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "LLM_",
        **COMMON_CONFIG,
    )

    host: IPvAnyAddress = Field(
        "127.0.0.1",
        description="Host of the local LLM server.",
    )
    port: int = Field(
        11434,
        description="Port of the local LLM server.",
        ge=1,
        le=65535,
    )


class Settings(BaseSettings):
    """Library configuration."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        **COMMON_CONFIG,
    )

    api: APISettings = Field(
        default_factory=APISettings,
        description="API settings.",
    )
    llm: LLMSettings = Field(
        default_factory=LLMSettings,
        description="LLM settings.",
    )
