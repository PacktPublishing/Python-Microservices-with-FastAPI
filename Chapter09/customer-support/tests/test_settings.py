import os
from unittest.mock import patch

from customer_support import Settings
from customer_support.config import ENV_PREFIX


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.api.port == 8009
    assert str(settings.api.host) == "127.0.0.1"


def test_settings_from_environment() -> None:
    with patch.dict(
        os.environ,
        {
            f"{ENV_PREFIX}API_PORT": "9000",
            f"{ENV_PREFIX}LLM_PORT": "9001",
            f"{ENV_PREFIX}API_HOST": "0.0.0.0",
            f"{ENV_PREFIX}LLM_HOST": "10.0.0.5",
        },
    ):
        settings = Settings()
        assert settings.api.port == 9000
        assert settings.llm.port == 9001
        assert str(settings.api.host) == "0.0.0.0"
        assert str(settings.llm.host) == "10.0.0.5"
