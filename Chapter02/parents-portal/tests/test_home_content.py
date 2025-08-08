import pytest
from syrupy.extensions.single_file import (
    SingleFileAmberSnapshotExtension,
)


@pytest.mark.parametrize("path", ["/home", "/"])
def test_home_content(test_client, path, snapshot):
    """Test that /home and / return the welcome page."""
    response = test_client.get(path)
    assert response.status_code == 200
    assert response.text == snapshot


@pytest.mark.parametrize(
    "path", ["/home/en", "/home/fr", "/home/it", "/home/pt"]
)
def test_home_with_different_languages(
    test_client, path, snapshot
):
    response = test_client.get(path)
    assert response.status_code == 200
    assert response.text == snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    )


def test_home_sets_and_uses_tracking_cookie(test_client):
    """Test that /home sets TRACKING cookie and shows welcome back message on repeat visit."""
    # First visit: should set cookie and show welcome
    response = test_client.get("/")
    assert response.status_code == 200
    assert "Welcome to the Portal" in response.text
    assert response.cookies.get("TRACKING") is not None

    # Second visit: should recognize cookie and show welcome back
    response = test_client.get("/")
    assert response.status_code == 200
    assert "Welcome back" in response.text
