"""
Tests for the get babysitter feature.
"""

from fastapi.testclient import TestClient


class TestGetBabysitter:
    def test_get_babysitter_success(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        # First create a babysitter
        create_response = client.post(
            "/api/v1/babysitters/",
            json=sample_babysitter_data,
        )
        created_id = create_response.json()["id"]

        # Then fetch it
        response = client.get(f"/api/v1/babysitters/{created_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["first_name"] == "Alice"

    def test_get_babysitter_not_found(self, client: TestClient):
        response = client.get(
            "/api/v1/babysitters/nonexistent-id-12345"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
