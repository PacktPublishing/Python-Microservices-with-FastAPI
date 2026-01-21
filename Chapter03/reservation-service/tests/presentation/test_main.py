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


def test_create_slot_empty_babysitter_name(test_client):
    payload = {
        "week_day": "monday",
        "time_slot": "morning",
        "babysitter_name": "   ",  # whitespace only - passes Pydantic but fails domain
    }

    response = test_client.post("/api/v1/slots", json=payload)

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


# --- List Available Slots Tests ---


def test_list_slots_empty(test_client):
    response = test_client.get("/api/v1/slots")

    assert response.status_code == 200
    assert response.json() == []


def test_list_slots_returns_available_slots(test_client):
    # Create a slot first
    create_payload = {
        "week_day": "monday",
        "time_slot": "morning",
        "babysitter_name": "Maria Rodriguez",
    }
    test_client.post("/api/v1/slots", json=create_payload)

    response = test_client.get("/api/v1/slots")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["week_day"] == "monday"
    assert data[0]["status"] == "available"


def test_list_slots_filter_by_week_day(test_client):
    # Create slots for different days
    test_client.post(
        "/api/v1/slots",
        json={
            "week_day": "monday",
            "time_slot": "morning",
            "babysitter_name": "Maria",
        },
    )
    test_client.post(
        "/api/v1/slots",
        json={
            "week_day": "tuesday",
            "time_slot": "morning",
            "babysitter_name": "John",
        },
    )

    response = test_client.get("/api/v1/slots?week_day=monday")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["week_day"] == "monday"


def test_list_slots_filter_by_time_slot(test_client):
    # Create slots for different time slots
    test_client.post(
        "/api/v1/slots",
        json={
            "week_day": "monday",
            "time_slot": "morning",
            "babysitter_name": "Maria",
        },
    )
    test_client.post(
        "/api/v1/slots",
        json={
            "week_day": "monday",
            "time_slot": "afternoon",
            "babysitter_name": "John",
        },
    )

    response = test_client.get("/api/v1/slots?time_slot=morning")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["time_slot"] == "morning"


# --- Reserve Slot Tests ---


def test_reserve_slot_success(test_client):
    # Create a slot first
    create_response = test_client.post(
        "/api/v1/slots",
        json={
            "week_day": "monday",
            "time_slot": "morning",
            "babysitter_name": "Maria Rodriguez",
        },
    )
    slot_id = create_response.json()["id"]

    reserve_payload = {
        "parent_email": "parent@example.com",
        "description": "Date night",
    }

    response = test_client.post(
        f"/api/v1/slots/{slot_id}/reserve", json=reserve_payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reserved"
    assert data["reservation_email"] == "parent@example.com"
    assert data["reservation_description"] == "Date night"
    assert data["reserved_at"] is not None


def test_reserve_slot_not_found(test_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    reserve_payload = {
        "parent_email": "parent@example.com",
        "description": "Date night",
    }

    response = test_client.post(
        f"/api/v1/slots/{fake_id}/reserve", json=reserve_payload
    )

    assert response.status_code == 404


def test_reserve_slot_already_reserved(test_client):
    # Create and reserve a slot
    create_response = test_client.post(
        "/api/v1/slots",
        json={
            "week_day": "monday",
            "time_slot": "morning",
            "babysitter_name": "Maria Rodriguez",
        },
    )
    slot_id = create_response.json()["id"]

    reserve_payload = {
        "parent_email": "parent@example.com",
        "description": "Date night",
    }
    test_client.post(
        f"/api/v1/slots/{slot_id}/reserve", json=reserve_payload
    )

    # Try to reserve again
    response = test_client.post(
        f"/api/v1/slots/{slot_id}/reserve", json=reserve_payload
    )

    assert response.status_code == 400


# --- Confirm Reservation Tests ---


def test_confirm_reservation_success(test_client):
    # Create and reserve a slot
    create_response = test_client.post(
        "/api/v1/slots",
        json={
            "week_day": "monday",
            "time_slot": "morning",
            "babysitter_name": "Maria Rodriguez",
        },
    )
    slot_id = create_response.json()["id"]

    test_client.post(
        f"/api/v1/slots/{slot_id}/reserve",
        json={
            "parent_email": "parent@example.com",
            "description": "",
        },
    )

    response = test_client.post(
        f"/api/v1/slots/{slot_id}/confirm"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["confirmed_at"] is not None


def test_confirm_reservation_not_found(test_client):
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = test_client.post(
        f"/api/v1/slots/{fake_id}/confirm"
    )

    assert response.status_code == 404


def test_confirm_reservation_not_reserved(test_client):
    # Create a slot but don't reserve it
    create_response = test_client.post(
        "/api/v1/slots",
        json={
            "week_day": "monday",
            "time_slot": "morning",
            "babysitter_name": "Maria Rodriguez",
        },
    )
    slot_id = create_response.json()["id"]

    response = test_client.post(
        f"/api/v1/slots/{slot_id}/confirm"
    )

    assert response.status_code == 400


# --- Refuse Reservation Tests ---


def test_refuse_reservation_success(test_client):
    # Create and reserve a slot
    create_response = test_client.post(
        "/api/v1/slots",
        json={
            "week_day": "monday",
            "time_slot": "morning",
            "babysitter_name": "Maria Rodriguez",
        },
    )
    slot_id = create_response.json()["id"]

    test_client.post(
        f"/api/v1/slots/{slot_id}/reserve",
        json={
            "parent_email": "parent@example.com",
            "description": "",
        },
    )

    response = test_client.post(f"/api/v1/slots/{slot_id}/refuse")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "available"
    assert data["reservation_email"] is None
    assert data["reservation_description"] is None


def test_refuse_reservation_not_found(test_client):
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = test_client.post(f"/api/v1/slots/{fake_id}/refuse")

    assert response.status_code == 404


def test_refuse_reservation_not_reserved(test_client):
    # Create a slot but don't reserve it
    create_response = test_client.post(
        "/api/v1/slots",
        json={
            "week_day": "monday",
            "time_slot": "morning",
            "babysitter_name": "Maria Rodriguez",
        },
    )
    slot_id = create_response.json()["id"]

    response = test_client.post(f"/api/v1/slots/{slot_id}/refuse")

    assert response.status_code == 400
