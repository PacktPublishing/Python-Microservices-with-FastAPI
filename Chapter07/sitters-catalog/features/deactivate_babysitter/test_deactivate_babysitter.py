"""
Tests for the deactivate babysitter feature.
"""

from fastapi.testclient import TestClient


class TestDeactivateBabysitter:
    def test_deactivate_babysitter_success(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        # Create a babysitter
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]
        assert create_response.json()["is_active"] is True

        # Deactivate it
        response = client.post(
            f"/api/v1/babysitters/{created_id}/deactivate"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["id"] == created_id

    def test_deactivate_babysitter_not_found(
        self, client: TestClient
    ):
        response = client.post(
            "/api/v1/babysitters/nonexistent-id/deactivate"
        )

        assert response.status_code == 404

    def test_deactivate_babysitter_idempotent(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        # Create a babysitter
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]

        # Deactivate twice
        client.post(
            f"/api/v1/babysitters/{created_id}/deactivate"
        )
        response = client.post(
            f"/api/v1/babysitters/{created_id}/deactivate"
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False
