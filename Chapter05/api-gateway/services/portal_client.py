from abc import ABC, abstractmethod
from typing import Literal

import httpx

Lang = Literal["en", "fr", "it", "pt"]


class PortalClientInterface(ABC):
    @abstractmethod
    async def get_home(
        self, lang: Lang = "en", name: str = ""
    ) -> str:
        """Get the home page content for a given language."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the portal service is healthy."""


class MockPortalClient(PortalClientInterface):
    def __init__(self):
        self.home_pages: dict[Lang, str] = {
            "en": "<h1>Welcome to Babysitting Service</h1>",
            "fr": "<h1>Bienvenue au Service de Garde</h1>",
            "it": "<h1>Benvenuti al Servizio di Babysitting</h1>",
            "pt": "<h1>Bem-vindo ao Serviço de Babá</h1>",
        }
        self.is_healthy: bool = True

    async def get_home(
        self, lang: Lang = "en", name: str = ""
    ) -> str:
        base_content = self.home_pages.get(
            lang, self.home_pages["en"]
        )
        if name:
            return base_content.replace(
                "</h1>", f", {name}!</h1>"
            )
        return base_content

    async def health_check(self) -> bool:
        return self.is_healthy


class PortalClient(PortalClientInterface):
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url

    async def get_home(
        self, lang: Lang = "en", name: str = ""
    ) -> str:
        async with httpx.AsyncClient() as client:
            params = {"name": name} if name else {}
            response = await client.get(
                f"{self.base_url}/home/{lang}",
                params=params,
            )
            response.raise_for_status()
            return response.text

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/")
                return response.status_code == 200
        except httpx.RequestError:
            return False
