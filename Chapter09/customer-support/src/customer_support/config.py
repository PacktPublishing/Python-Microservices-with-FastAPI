__all__ = ["Settings"]


from pydantic import Field, IPvAnyAddress
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "CUSTOMER_SUPPORT_"
COMMON_CONFIG = {
    "case_sensitive": False,  # from the environment
    "env_file_encoding": "utf-8",
    "env_file": ".env",
    "extra": "ignore",
    "env_nested_delimiter": "_",
    "validate_assignment": True,
}


class APISettings(BaseSettings):
    """API settings."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "API_",
        **COMMON_CONFIG,  # type: ignore
    )

    host: IPvAnyAddress = Field(
        "0.0.0.0",
        description="Webservice bind host. Defaults to 0.0.0.0 to accept connections from all interfaces.",
    )
    port: int = Field(
        8000,
        description="Webservice port.",
        ge=0,
    )


class LLMSettings(BaseSettings):
    """LLM settings."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX + "LLM_",
        **COMMON_CONFIG,  # type: ignore
    )

    hf_token_key: str = Field(
        "HF_TOKEN",
        description="Name of the environment variable that contains the HuggingFace token.",
    )
    default_llm_id: str = Field(
        "TinyLlama/TinyLlama_v1.1",
        description="Default LLM.",
    )
    default_llm_mlx_id: str = Field(
        "mlx-community/quantized-gemma-2b-it",
        description="Default LLM MLX. For more all available LLMs, see: https://huggingface.co/mlx-community",
    )
    system_prompt: str = Field(
        """
        You are the customer support for a baby-sitting app.
        """,
        description="System prompt for LLM.",
    )
    bind_host: IPvAnyAddress = Field(
        "0.0.0.0",
        description="Host the LLM server binds to. Defaults to 0.0.0.0 to listen on all interfaces.",
    )
    host: IPvAnyAddress = Field(
        "127.0.0.1",
        description=(
            "Host the API container connects to when calling the LLM server. "
            "Defaults to 127.0.0.1 (loopback), which works when both services run on the same machine."
        ),
    )
    port: int = Field(
        8080,
        description="Port number for the LLM server.",
        ge=0,
    )

    @property
    def llm_server(self) -> str:
        """LLM server URL."""
        return f"http://{self.host}:{self.port}/v1"


class Settings(BaseSettings):
    """Library cofiguration."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        **COMMON_CONFIG,  # type: ignore
    )

    api: APISettings = Field(
        default_factory=APISettings,
        description="API settings.",
    )
    llm: LLMSettings = Field(
        default_factory=LLMSettings,
        description="LLM settings.",
    )
