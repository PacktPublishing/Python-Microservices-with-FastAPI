from pathlib import Path

import pytest


@pytest.fixture
def tests_dir() -> Path:
    """Location to this `tests` folder."""
    return Path(__file__).parent
