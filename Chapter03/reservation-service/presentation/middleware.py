import logging

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("uvicorn")


class StateCheckMiddleware:
    def __init__(
        self, app: ASGIApp, context_name: str = ""
    ) -> None:
        self.app = app
        self.context_name = context_name

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope.get("type") == "http":
            state = scope.get("state")
            logger.info(state)
        await self.app(scope, receive, send)
