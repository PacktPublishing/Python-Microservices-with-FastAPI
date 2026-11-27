import pytest
from fastapi.testclient import TestClient


def test_weekly_activity(client: TestClient) -> None:
    """The weekly endpoint returns one row per week with a share."""
    weeks = client.get("/activity/weekly").json()
    assert weeks, "the simulated year should have weeks"
    assert all(0 <= w["confirmation_rate"] <= 1 for w in weeks), (
        "confirmation rates should be shares"
    )


def test_slot_demand(
    client: TestClient,
    week_days: list[str],
) -> None:
    """The slots endpoint returns the days in calendar order."""
    rows = client.get("/activity/slots").json()
    assert [row["week_day"] for row in rows] == week_days, (
        "every day should appear once, in order"
    )


def test_weekly_chart(
    client: TestClient,
    png_signature: bytes,
) -> None:
    """The chart endpoint returns a PNG image."""
    response = client.get("/charts/weekly.png")
    assert response.headers["content-type"] == "image/png", (
        "the chart should be served as PNG"
    )
    assert response.content.startswith(png_signature), (
        "the body should be a PNG file"
    )


def test_at_risk_is_sorted(
    client: TestClient,
    limit: int,
) -> None:
    """The at-risk endpoint returns `limit` parents, riskiest first."""
    parents = client.get(
        "/parents/at-risk",
        params={"limit": limit},
    ).json()
    risks = [parent["risk"] for parent in parents]
    assert len(risks) == limit, "the limit should be respected"
    assert risks == sorted(risks, reverse=True), (
        "parents should be sorted by decreasing risk"
    )


def test_risk_of_one_parent(client: TestClient) -> None:
    """The risk of the riskiest parent matches the at-risk list."""
    riskiest = client.get(
        "/parents/at-risk",
        params={"limit": 1},
    ).json()[0]
    response = client.get(
        f"/parents/{riskiest['parent_id']}/risk",
    )
    assert response.json() == riskiest, "both routes should agree"


def test_risk_of_unknown_parent(
    client: TestClient,
    unknown_parent: int,
) -> None:
    """An unknown or inactive parent returns 404."""
    response = client.get(f"/parents/{unknown_parent}/risk")
    assert response.status_code == 404, "the parent is not active"


def test_quality_reports(client: TestClient) -> None:
    """The quality endpoint reports the drift check as passing."""
    reports = client.get("/quality").json()
    assert {r["check"] for r in reports} == {"drift"}
    assert all(r["ok"] for r in reports), (
        f"checks failed: {reports}"
    )


def test_refresh(client: TestClient) -> None:
    """Refreshing reloads the data and returns no content."""
    assert client.post("/refresh").status_code == 204, (
        "refresh should succeed without a body"
    )


def test_frontend(client: TestClient, page: str) -> None:
    """The built frontend is served at `/app/`."""
    response = client.get("/app/")
    assert response.text == page, "/app/ should serve index.html"


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
