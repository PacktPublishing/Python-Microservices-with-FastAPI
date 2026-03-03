"""
Tests for the list babysitters feature.
"""

from fastapi.testclient import TestClient


class TestListBabysitters:
    def test_list_babysitters_empty(self, client: TestClient):
        response = client.get("/api/v1/babysitters/")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_babysitters_returns_all(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        # Create two babysitters
        client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        response = client.get("/api/v1/babysitters/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_babysitters_filter_by_city(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        response = client.get("/api/v1/babysitters/?city=Paris")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["location"]["city"] == "Paris"

    def test_list_babysitters_filter_by_min_rate(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        response = client.get("/api/v1/babysitters/?min_rate=20")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["hourly_rate"] >= 20

    def test_list_babysitters_filter_by_max_rate(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        response = client.get("/api/v1/babysitters/?max_rate=20")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["hourly_rate"] <= 20

    def test_list_babysitters_filter_by_rate_range(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        response = client.get(
            "/api/v1/babysitters/?min_rate=15&max_rate=20"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert 15 <= data[0]["hourly_rate"] <= 20

    def test_list_babysitters_filter_by_language(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        response = client.get(
            "/api/v1/babysitters/?language=French"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "French" in data[0]["languages"]

    def test_list_babysitters_filter_by_min_experience(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        response = client.get(
            "/api/v1/babysitters/?min_experience=8"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["years_of_experience"] >= 8

    def test_list_babysitters_filter_by_is_active(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
    ):
        # Create and deactivate a babysitter
        create_response = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        created_id = create_response.json()["id"]
        client.post(
            f"/api/v1/babysitters/{created_id}/deactivate"
        )

        # By default, list returns only active
        response = client.get("/api/v1/babysitters/")
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Explicitly request inactive
        response = client.get(
            "/api/v1/babysitters/?is_active=false"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_active"] is False

    def test_list_babysitters_pagination_skip(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        response = client.get("/api/v1/babysitters/?skip=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_babysitters_pagination_limit(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        response = client.get("/api/v1/babysitters/?limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_babysitters_combined_filters(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        response = client.get(
            "/api/v1/babysitters/"
            "?city=Paris&language=French&min_experience=3"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["location"]["city"] == "Paris"
