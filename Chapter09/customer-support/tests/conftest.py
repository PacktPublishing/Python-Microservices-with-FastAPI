from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from customer_support.api import app


@pytest.fixture
def tests_dir() -> Path:
    """Location to this `tests` folder."""
    return Path(__file__).parent


@pytest.fixture
def client() -> TestClient:
    """Test client for the customer support API."""
    return TestClient(app)
