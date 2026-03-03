"""
Tests for the get featured babysitters feature.
"""

from fastapi.testclient import TestClient


class TestGetFeaturedBabysitters:
    def test_get_featured_empty(self, client: TestClient):
        response = client.get("/api/v1/babysitters/featured")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_featured_returns_active_only(
        self,
        client: TestClient,
        sample_babysitter_data: dict,
        another_babysitter_data: dict,
    ):
        # Create two babysitters
        response1 = client.post(
            "/api/v1/babysitters/", json=sample_babysitter_data
        )
        client.post(
            "/api/v1/babysitters/", json=another_babysitter_data
        )

        # Deactivate the first one
        created_id = response1.json()["id"]
        client.post(
            f"/api/v1/babysitters/{created_id}/deactivate"
        )

        # Featured should only return the active one
        response = client.get("/api/v1/babysitters/featured")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_active"] is True

    def test_get_featured_sorted_by_experience(
        self, client: TestClient
    ):
        # Create babysitters with different experience levels
        babysitters = [
            {
                "first_name": f"Sitter{i}",
                "last_name": "Test",
                "age": 25,
                "hourly_rate": 15.00,
                "years_of_experience": exp,
                "contact": {"email": f"sitter{i}@example.com"},
                "location": {
                    "city": "Paris",
                    "country": "France",
                },
            }
            for i, exp in enumerate([3, 10, 5, 8, 1])
        ]

        for sitter in babysitters:
            client.post("/api/v1/babysitters/", json=sitter)

        response = client.get("/api/v1/babysitters/featured")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        # Should be sorted by experience descending
        experiences = [d["years_of_experience"] for d in data]
        assert experiences == sorted(experiences, reverse=True)

    def test_get_featured_limits_to_5(self, client: TestClient):
        # Create more than 5 babysitters
        for i in range(8):
            sitter = {
                "first_name": f"Sitter{i}",
                "last_name": "Test",
                "age": 25,
                "hourly_rate": 15.00,
                "years_of_experience": i,
                "contact": {"email": f"sitter{i}@example.com"},
                "location": {
                    "city": "Paris",
                    "country": "France",
                },
            }
            client.post("/api/v1/babysitters/", json=sitter)

        response = client.get("/api/v1/babysitters/featured")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # Limited to 5

        # Should have the top 5 most experienced (7, 6, 5, 4, 3)
        experiences = [d["years_of_experience"] for d in data]
        assert experiences == [7, 6, 5, 4, 3]
