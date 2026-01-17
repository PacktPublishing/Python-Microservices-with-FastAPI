def test_health_check(test_client):
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "babysitter-reservation-api"


def test_create_slot_success(test_client):
    payload = {
        "week_day": "monday",
        "time_slot": "morning",
        "babysitter_name": "Maria Rodriguez",
    }

    response = test_client.post("/api/v1/slots", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["week_day"] == "monday"
    assert data["time_slot"] == "morning"
    assert data["babysitter_name"] == "Maria Rodriguez"
    assert data["status"] == "available"
    assert data["reservation_email"] is None
    assert data["reservation_description"] is None
    assert data["reserved_at"] is None
    assert data["confirmed_at"] is None
    assert "id" in data


def test_create_slot_invalid_week_day(test_client):
    payload = {
        "week_day": "invalid_day",
        "time_slot": "morning",
        "babysitter_name": "Maria Rodriguez",
    }

    response = test_client.post("/api/v1/slots", json=payload)

    assert response.status_code == 422


def test_create_slot_invalid_time_slot(test_client):
    payload = {
        "week_day": "monday",
        "time_slot": "invalid_slot",
        "babysitter_name": "Maria Rodriguez",
    }

    response = test_client.post("/api/v1/slots", json=payload)

    assert response.status_code == 422


def test_create_slot_missing_field(test_client):
    payload = {
        "week_day": "monday",
        "time_slot": "morning",
        # missing babysitter_name
    }

    response = test_client.post("/api/v1/slots", json=payload)

    assert response.status_code == 422
