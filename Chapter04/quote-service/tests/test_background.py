from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from main import app


def test_background_task_logs_quote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with TestClient(app) as client:
        response = client.get("/quote/async")
    assert response.status_code == 200
    log = Path("served.log").read_text()
    assert response.json()["quote"] in log
