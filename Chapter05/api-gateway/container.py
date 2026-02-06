from dependency_injector import containers, providers

from services import (
    MockPortalClient,
    MockReservationClient,
    PortalClient,
    ReservationClient,
)


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["config.yaml"])

    portal_client = providers.Selector(
        config.services.use_mocks,
        true=providers.Singleton(MockPortalClient),
        false=providers.Singleton(
            PortalClient,
            base_url=config.services.portal.base_url,
        ),
    )

    reservation_client = providers.Selector(
        config.services.use_mocks,
        true=providers.Singleton(
            MockReservationClient, prefill=True
        ),
        false=providers.Singleton(
            ReservationClient,
            base_url=config.services.reservations.base_url,
        ),
    )
