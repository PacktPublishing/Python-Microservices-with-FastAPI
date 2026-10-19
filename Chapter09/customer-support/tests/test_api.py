import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    """Test the health endpoint returns an `ok` status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
