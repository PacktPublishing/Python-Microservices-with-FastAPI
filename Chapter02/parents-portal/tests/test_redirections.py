def test_root_redirects_to_home(test_client):
    """Test that / redirects to /home with 307 status."""
    response = test_client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "home/en"


def test_root_with_name_redirects_to_home(test_client):
    """Test that / redirects to /home with 307 status."""
    response = test_client.get(
        "/home", params={"name": "John"}, follow_redirects=False
    )
    assert response.status_code == 307
    assert response.headers["location"] == "/home/en?name=John"


def test_root_with_language_and_name_redirects_to_home(
    test_client,
):
    """Test that / redirects to /home with 307 status."""
    response = test_client.get(
        "/pt", params={"name": "John"}, follow_redirects=False
    )
    assert response.status_code == 307
    assert response.headers["location"] == "/home/pt?name=John"
