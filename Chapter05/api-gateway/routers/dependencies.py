from fastapi import Request

from services import (
    PortalClientInterface,
    ReservationClientInterface,
)


def get_portal_client(request: Request) -> PortalClientInterface:
    return request.state.portal_client


def get_reservation_client(
    request: Request,
) -> ReservationClientInterface:
    return request.state.reservation_client
