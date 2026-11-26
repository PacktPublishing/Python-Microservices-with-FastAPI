import httpx2
from loguru import logger
from nicegui import app, ui

from .client import AnalyticsClient
from .config import Settings
from .dashboard import create_dashboard


def main() -> None:
    """Serve the dashboard until interrupted.

    Run it with `python -m analytics_dashboard`.
    """
    settings = Settings()
    client = httpx2.AsyncClient(
        base_url=str(settings.api_url),
        timeout=settings.timeout,
    )
    app.on_shutdown(client.aclose)
    create_dashboard(AnalyticsClient(client), settings.limit)
    logger.info("Dashboard on port {}", settings.port)
    ui.run(
        host=str(settings.host),
        port=settings.port,
        reload=False,
        show=False,
    )


if __name__ == "__main__":
    main()
