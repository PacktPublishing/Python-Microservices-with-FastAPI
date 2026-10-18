import os
from unittest.mock import patch

import pytest
from loguru import logger

from customer_support import Settings
from customer_support.config import ENV_PREFIX


def test_settings() -> None:
    """Test `Settings` class can use environment variables."""
    with patch.dict(
        os.environ,
        {
            f"{ENV_PREFIX}API_PORT": "8000",
            f"{ENV_PREFIX}LLM_PORT": "8001",
            f"{ENV_PREFIX}API_HOST": "0.0.0.0",
            f"{ENV_PREFIX}LLM_HOST": "0.0.0.0",
        },
    ):
        settings = Settings()
        assert settings.api.port == 8000
        assert settings.llm.port == 8001
        assert settings.api.host.__str__() == "0.0.0.0"
        assert settings.llm.host.__str__() == "0.0.0.0"
    logger.success("PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
