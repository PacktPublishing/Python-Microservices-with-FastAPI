import datetime

from freezegun import freeze_time


def test_home_with_name_sets_and_uses_tracking_cookie(
    test_client,
):
    """Test that /home sets TRACKING cookie and shows welcome back message on repeat visit."""
    response = test_client.get("/home", params={"name": "John"})
    assert response.status_code == 200
    assert "Welcome to the Portal" in response.text
    assert response.cookies.get("TRACKING") is not None

    response = test_client.get("/home", params={"name": "John"})
    assert response.status_code == 200
    assert "Hello John!" in response.text
    assert "Welcome back" in response.text


def test_home_with_cookie_expired(test_client):
    from app.home import COOKIE_EXPIRATION_TIME

    response = test_client.get("/home")
    assert response.status_code == 200
    assert response.cookies.get("TRACKING") is not None
    assert "Welcome to the Portal" in response.text

    # Advance time by expiration + 1 second so the cookie expires
    with freeze_time(
        datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(seconds=COOKIE_EXPIRATION_TIME + 1)
    ):
        response = test_client.get("/home")
        assert "Welcome to the Portal" in response.text
