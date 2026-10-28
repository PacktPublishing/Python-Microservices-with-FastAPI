import os
from unittest.mock import patch

import pytest

from customer_support import Settings
from customer_support.config import ENV_PREFIX, LLMSettings


def test_settings_defaults() -> None:
    """Test `Settings` falls back to its defaults when no environment variable is set."""
    settings = Settings()
    assert settings.api.port == 8009
    assert str(settings.api.host) == "127.0.0.1"


def test_settings_from_environment() -> None:
    """Test `Settings` can be overridden through environment variables."""
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


def test_model_settings_from_environment(
    changed_llm_environment: LLMSettings,
) -> None:
    """Read provider, model and both budgets through nested settings."""
    assert Settings().llm == changed_llm_environment, (
        "All LLM options must come from the environment."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
