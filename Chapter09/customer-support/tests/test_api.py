import pytest
from fastapi.testclient import TestClient

from customer_support.api import app


def test_health() -> None:
    """Test the health endpoint returns an `ok` status."""
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
