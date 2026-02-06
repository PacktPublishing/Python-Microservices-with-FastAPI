from main import app


class TestAppConfiguration:
    """Tests for app configuration."""

    def test_app_title(self):
        """Test app has correct title."""
        assert app.title == "Babysitting API Gateway"

    def test_app_version(self):
        """Test app has correct version."""
        assert app.version == "1.0.0"

    def test_app_has_description(self):
        """Test app has description."""
        assert app.description is not None
        assert "API Gateway" in app.description
