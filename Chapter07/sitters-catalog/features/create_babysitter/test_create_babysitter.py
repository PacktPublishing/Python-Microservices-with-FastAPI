"""
Tests for the create babysitter feature.
"""

from fastapi.testclient import TestClient


class TestCreateBabysitter:
    def test_create_babysitter_success(
        self, client: TestClient, sample_babysitter_data: dict
    ):
        response = client.post(
            "/api/v1/babysitters/",
            json=sample_babysitter_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Dupont"
        assert data["age"] == 28
        assert data["hourly_rate"] == 18.50
        assert data["years_of_experience"] == 5
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_babysitter_minimal_data(
        self, client: TestClient
    ):
        minimal_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "age": 18,
            "hourly_rate": 10.00,
            "years_of_experience": 0,
            "contact": {"email": "jane@example.com"},
            "location": {"city": "Berlin", "country": "Germany"},
        }

        response = client.post(
            "/api/v1/babysitters/",
            json=minimal_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["languages"] == []
        assert data["certifications"] == []
        assert data["availability"] == []

    def test_create_babysitter_invalid_age(
        self, client: TestClient
    ):
        invalid_data = {
            "first_name": "Young",
            "last_name": "Person",
            "age": 16,  # Too young, must be >= 18
            "hourly_rate": 10.00,
            "years_of_experience": 0,
            "contact": {"email": "young@example.com"},
            "location": {"city": "Rome", "country": "Italy"},
        }

        response = client.post(
            "/api/v1/babysitters/",
            json=invalid_data,
        )

        assert response.status_code == 422

    def test_create_babysitter_invalid_hourly_rate(
        self, client: TestClient
    ):
        invalid_data = {
            "first_name": "Free",
            "last_name": "Worker",
            "age": 20,
            "hourly_rate": 0,  # Must be > 0
            "years_of_experience": 0,
            "contact": {"email": "free@example.com"},
            "location": {"city": "Rome", "country": "Italy"},
        }

        response = client.post(
            "/api/v1/babysitters/",
            json=invalid_data,
        )

        assert response.status_code == 422

    def test_create_babysitter_negative_experience(
        self, client: TestClient
    ):
        invalid_data = {
            "first_name": "Negative",
            "last_name": "Experience",
            "age": 20,
            "hourly_rate": 15.00,
            "years_of_experience": -1,  # Must be >= 0
            "contact": {"email": "neg@example.com"},
            "location": {"city": "Rome", "country": "Italy"},
        }

        response = client.post(
            "/api/v1/babysitters/",
            json=invalid_data,
        )

        assert response.status_code == 422

    def test_create_babysitter_invalid_email(
        self, client: TestClient
    ):
        invalid_data = {
            "first_name": "Bad",
            "last_name": "Email",
            "age": 20,
            "hourly_rate": 15.00,
            "years_of_experience": 0,
            "contact": {"email": "not-an-email"},
            "location": {"city": "Rome", "country": "Italy"},
        }

        response = client.post(
            "/api/v1/babysitters/",
            json=invalid_data,
        )

        assert response.status_code == 422

    def test_create_babysitter_missing_required_fields(
        self, client: TestClient
    ):
        incomplete_data = {"first_name": "Only"}

        response = client.post(
            "/api/v1/babysitters/",
            json=incomplete_data,
        )

        assert response.status_code == 422

    def test_create_babysitter_invalid_availability_day(
        self, client: TestClient
    ):
        invalid_data = {
            "first_name": "Bad",
            "last_name": "Day",
            "age": 20,
            "hourly_rate": 15.00,
            "years_of_experience": 0,
            "availability": [
                {"day": "Funday", "from_hour": 8, "to_hour": 18}
            ],
            "contact": {"email": "bad@example.com"},
            "location": {"city": "Rome", "country": "Italy"},
        }

        response = client.post(
            "/api/v1/babysitters/",
            json=invalid_data,
        )

        assert response.status_code == 422

    def test_create_babysitter_invalid_availability_hour(
        self, client: TestClient
    ):
        invalid_data = {
            "first_name": "Bad",
            "last_name": "Hour",
            "age": 20,
            "hourly_rate": 15.00,
            "years_of_experience": 0,
            "availability": [
                {"day": "Monday", "from_hour": 25, "to_hour": 18}
            ],
            "contact": {"email": "bad@example.com"},
            "location": {"city": "Rome", "country": "Italy"},
        }

        response = client.post(
            "/api/v1/babysitters/",
            json=invalid_data,
        )

        assert response.status_code == 422
