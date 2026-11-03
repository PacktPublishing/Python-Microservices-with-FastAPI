from unittest.mock import Mock
from uuid import UUID

import httpx2
import pytest
from fastapi.testclient import TestClient

from customer_support.api import app
from customer_support.chat import SupportChat


def test_health(client: TestClient) -> None:
    """Test the health endpoint returns an `ok` status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.usefixtures("ingestion_environment")
def test_sync_endpoint_reports_changes(
    client: TestClient, sample_sources: list[str]
) -> None:
    """Sync twice through the API and read both reports."""
    first = client.post("/knowledge/sync")
    assert first.status_code == 200
    assert first.json()["added"] == sample_sources, (
        "The first sync must add every sample document."
    )
    second = client.post("/knowledge/sync").json()
    assert second["unchanged"] == sample_sources, (
        "The second sync must find nothing to re-embed."
    )


@pytest.mark.usefixtures("service_environment")
def test_lifespan_opens_the_service() -> None:
    """Start and stop the app with its real dependencies."""
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert isinstance(app.state.chat, SupportChat)


async def test_ask_streams_and_saves_the_answer(
    chat_client: httpx2.AsyncClient,
    chat: SupportChat,
    user_id: str,
    retrieval_query: str,
    reply_text: str,
    search_stub: Mock,
) -> None:
    """Stream an answer, then find the turn in the history."""
    headers = {"X-User-Id": user_id}
    created = await chat_client.post(
        "/conversations", headers=headers
    )
    assert created.status_code == 201
    conversation_id = UUID(created.json()["id"])
    response = await chat_client.post(
        f"/conversations/{conversation_id}/messages",
        headers=headers,
        json={
            "question": retrieval_query,
            "expected_position": 0,
        },
    )
    assert response.status_code == 200
    assert response.text == reply_text, (
        "The streamed body must be the model's answer."
    )
    search_stub.search.assert_called_once()
    history = await chat.repository.load(user_id, conversation_id)
    assert history is not None and history.messages, (
        "The streamed turn must be saved."
    )


async def test_ask_rejects_foreign_and_stale_requests(
    chat_client: httpx2.AsyncClient,
    user_id: str,
    other_user_id: str,
    retrieval_query: str,
) -> None:
    """Return 404 for another user's conversation, 409 when stale."""
    created = await chat_client.post(
        "/conversations", headers={"X-User-Id": user_id}
    )
    url = f"/conversations/{created.json()['id']}/messages"
    body = {"question": retrieval_query, "expected_position": 0}
    foreign = await chat_client.post(
        url, headers={"X-User-Id": other_user_id}, json=body
    )
    assert foreign.status_code == 404
    stale = await chat_client.post(
        url,
        headers={"X-User-Id": user_id},
        json=body | {"expected_position": 3},
    )
    assert stale.status_code == 409


def test_ask_requires_a_user(client: TestClient) -> None:
    """Reject requests without the identity header."""
    response = client.post("/conversations")
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
