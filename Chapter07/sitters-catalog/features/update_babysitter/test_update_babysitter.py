"""
Tests for the update babysitter feature.
"""

from fastapi.testclient import TestClient


class TestUpdateBabysitter:
    def test_put_update_babysitter_success(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        # Create a babysitter
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]

        # Full update
        update_data = {
            "first_name": "Alice Updated",
            "hourly_rate": 22.00,
        }
        response = client.put(
            f"/api/v1/babysitters/{created_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Alice Updated"
        assert data["hourly_rate"] == 22.00
        # Unchanged fields should remain
        assert data["last_name"] == "Dupont"

    def test_patch_update_babysitter_partial(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        # Create a babysitter
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]

        # Partial update with PATCH
        update_data = {"bio": "Updated bio only"}
        response = client.patch(
            f"/api/v1/babysitters/{created_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Updated bio only"
        # Other fields unchanged
        assert data["first_name"] == "Alice"
        assert data["hourly_rate"] == 18.50

    def test_update_babysitter_not_found(
        self, client: TestClient
    ):
        update_data = {"first_name": "Ghost"}

        response = client.put(
            "/api/v1/babysitters/nonexistent-id",
            json=update_data,
        )

        assert response.status_code == 404

    def test_patch_babysitter_not_found(self, client: TestClient):
        update_data = {"first_name": "Ghost"}

        response = client.patch(
            "/api/v1/babysitters/nonexistent-id",
            json=update_data,
        )

        assert response.status_code == 404

    def test_update_babysitter_invalid_age(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]

        update_data = {"age": 15}  # Invalid, must be >= 18

        response = client.put(
            f"/api/v1/babysitters/{created_id}",
            json=update_data,
        )

        assert response.status_code == 422

    def test_update_babysitter_invalid_hourly_rate(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]

        update_data = {"hourly_rate": -5}  # Invalid, must be > 0

        response = client.put(
            f"/api/v1/babysitters/{created_id}",
            json=update_data,
        )

        assert response.status_code == 422

    def test_update_babysitter_location(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]

        update_data = {
            "location": {"city": "Nice", "country": "France"}
        }

        response = client.patch(
            f"/api/v1/babysitters/{created_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["location"]["city"] == "Nice"

    def test_update_babysitter_contact(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]

        update_data = {
            "contact": {"email": "newemail@example.com"}
        }

        response = client.patch(
            f"/api/v1/babysitters/{created_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["contact"]["email"] == "newemail@example.com"

    def test_update_babysitter_languages(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]

        update_data = {
            "languages": ["English", "French", "German"]
        }

        response = client.patch(
            f"/api/v1/babysitters/{created_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert "German" in data["languages"]

    def test_update_babysitter_is_active(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]

        update_data = {"is_active": False}

        response = client.patch(
            f"/api/v1/babysitters/{created_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
