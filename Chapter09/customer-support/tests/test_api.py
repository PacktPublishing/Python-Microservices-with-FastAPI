import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    """Test the health endpoint returns an `ok` status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.usefixtures("ingestion_environment")
def test_sync_endpoint_reports_changes(
    client: TestClient, sample_sources: list[str]
) -> None:
    """Sync twice through the API and read both reports."""
    first = client.post("/knowledge/sync")
    assert first.status_code == 200
    assert first.json()["added"] == sample_sources, (
        "The first sync must add every sample document."
    )
    second = client.post("/knowledge/sync").json()
    assert second["unchanged"] == sample_sources, (
        "The second sync must find nothing to re-embed."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
