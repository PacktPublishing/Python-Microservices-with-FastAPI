"""
Unit tests for config.py

Uses monkeypatch to inject environment variables
without touching a real .env
file or polluting the test process environment.
"""

import pytest

from config import Settings


class TestSettings:
    def test_default_mongo_uri(self) -> None:
        s = Settings()
        assert s.mongo_uri == "mongodb://localhost:27017"

    def test_default_app_title(self) -> None:
        s = Settings()
        assert s.app_title == "Babysitter Catalog API"

    def test_default_debug_is_false(self) -> None:
        s = Settings()
        assert s.debug is False

    def test_mongo_uri_overridden_by_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(
            "MONGO_URI", "mongodb://remotehost:27017"
        )
        s = Settings()
        assert s.mongo_uri == "mongodb://remotehost:27017"

    def test_db_name_overridden_by_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DB_NAME", "test_catalog")
        s = Settings()
        assert s.db_name == "test_catalog"

    def test_debug_true_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEBUG", "true")
        s = Settings()
        assert s.debug is True

    def test_debug_false_from_env_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEBUG", "false")
        s = Settings()
        assert s.debug is False

    def test_app_title_overridden_by_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("APP_TITLE", "My Custom API")
        s = Settings()
        assert s.app_title == "My Custom API"

    def test_multiple_env_vars_applied_together(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MONGO_URI", "mongodb://host:9999")
        monkeypatch.setenv("DB_NAME", "staging")
        monkeypatch.setenv("DEBUG", "1")
        s = Settings()
        assert s.mongo_uri == "mongodb://host:9999"
        assert s.db_name == "staging"
        assert s.debug is True
