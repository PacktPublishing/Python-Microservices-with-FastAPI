"""
Tests for the delete babysitter feature.
"""

from fastapi.testclient import TestClient


class TestDeleteBabysitter:
    def test_delete_babysitter_success(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        # Create a babysitter
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]

        # Delete it
        response = client.delete(
            f"/api/v1/babysitters/{created_id}"
        )

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/babysitters/{created_id}"
        )
        assert get_response.status_code == 404

    def test_delete_babysitter_not_found(
        self, client: TestClient
    ):
        response = client.delete(
            "/api/v1/babysitters/nonexistent-id"
        )

        assert response.status_code == 404
