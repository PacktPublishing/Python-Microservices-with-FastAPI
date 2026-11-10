from uuid import UUID

import httpx2
from loguru import logger
from pydantic import BaseModel

from .config import SupportSettings


class SupportAnswer(BaseModel):
    """The support assistant's answer and the conversation holding it."""

    conversation_id: UUID
    text: str


class Conversation(BaseModel):
    """The part of a created conversation the client needs."""

    id: UUID


class SupportError(RuntimeError):
    """The support service could not answer the question."""


def support_client(
    settings: SupportSettings, auth: httpx2.Auth | None = None
) -> httpx2.AsyncClient:
    """Create an HTTP client for the support service.

    Args:
        settings (SupportSettings):
            Address and timeout of the support service.

        auth (httpx2.Auth | None):
            Optional hook that adds credentials to every request.

    Returns:
        httpx2.AsyncClient:
            A client whose relative URLs point at the support service.
    """
    return httpx2.AsyncClient(
        base_url=str(settings.url),
        timeout=settings.timeout,
        auth=auth,
    )


class SupportService:
    """Ask the support service questions on behalf of a user."""

    def __init__(self, client: httpx2.AsyncClient) -> None:
        """Receive the HTTP client rather than creating one.

        Args:
            client (httpx2.AsyncClient):
                Client configured for the support service.
        """
        self.client = client

    async def ask(
        self, user_id: str, question: str
    ) -> SupportAnswer:
        """Ask a question in a new conversation owned by `user_id`.

        Args:
            user_id (str):
                Identity forwarded to the support service.

            question (str):
                The question to answer.

        Returns:
            SupportAnswer:
                The full answer and the conversation it belongs to.

        Raises:
            SupportError:
                The service timed out, failed or could not be reached.
        """
        headers = {"X-User-Id": user_id}
        try:
            created = await self.client.post(
                "/conversations", headers=headers
            )
            created.raise_for_status()
            conversation = Conversation.model_validate_json(
                created.content
            )
            reply = await self.client.post(
                f"/conversations/{conversation.id}/messages",
                headers=headers,
                json={
                    "question": question,
                    "expected_position": 0,
                },
            )
            reply.raise_for_status()
        except httpx2.TimeoutException as error:
            raise SupportError("Support timed out") from error
        except httpx2.HTTPStatusError as error:
            status = error.response.status_code
            raise SupportError(
                f"Support failed ({status})"
            ) from error
        except httpx2.HTTPError as error:
            raise SupportError(
                "Support is unreachable"
            ) from error
        logger.debug(
            "Answered in conversation {}", conversation.id
        )
        return SupportAnswer(
            conversation_id=conversation.id, text=reply.text
        )
