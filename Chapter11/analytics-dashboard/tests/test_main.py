from unittest.mock import MagicMock

import pytest

from analytics_dashboard.__main__ import main
from analytics_dashboard.config import Settings

pytestmark = pytest.mark.nicegui_main_file("")


@pytest.mark.usefixtures("user")
async def test_main_serves_the_dashboard(
    run: MagicMock,
    settings: Settings,
) -> None:
    """`main` starts NiceGUI on the configured address."""
    main()
    run.assert_called_once()
    assert run.call_args.kwargs["port"] == settings.port, (
        "the dashboard should listen on the configured port"
    )
    assert run.call_args.kwargs["host"] == str(settings.host), (
        "the dashboard should listen on the configured host"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-x", "-s"])
