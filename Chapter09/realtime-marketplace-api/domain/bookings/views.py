import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from domain.notifications.repositories import NotificationRepository
from domain.notifications.schemas import NotificationCreate
from domain.notifications.services import NotificationService
from domain.notifications.types import NotificationType
from domain.user.dependencies import get_current_user, get_user_from_token
from domain.user.models import User
from domain.user.repositories import UserRepository
from infrastructure.celery.tasks import (
    send_booking_confirmation_to_parent,
    send_booking_notification_to_sitter,
)
from infrastructure.database.session import get_async_session, local_session
from infrastructure.websocket.connection_manager import manager

from .repositories import BookingRepository
from .schemas import BookingCreate, BookingRead
from .types import BookingStatus

router = APIRouter(prefix="/bookings", tags=["bookings"])


def get_booking_repository() -> BookingRepository:
    """Get booking repository instance."""
    return BookingRepository()


def get_user_repository() -> UserRepository:
    """Get user repository instance."""
    return UserRepository()


@router.post("/", response_model=BookingRead, status_code=201)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    booking_repo: BookingRepository = Depends(get_booking_repository),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Create a new booking."""
    sitter = await user_repo.get(session, id=booking_data.sitter_id)
    if not sitter:
        raise HTTPException(status_code=404, detail="Sitter not found")

    new_booking = await booking_repo.create(
        session=session,
        booking_data=booking_data,
        parent_id=current_user.id,
    )

    send_booking_confirmation_to_parent.delay(
        booking_id=new_booking.id,
        parent_email=current_user.email,
        parent_name=current_user.name,
        sitter_name=sitter.name,
        booking_time=new_booking.start_time.strftime(
            "%B %d, %Y at %I:%M %p"
        ),
    )

    send_booking_notification_to_sitter.delay(
        booking_id=new_booking.id,
        sitter_email=sitter.email,
        sitter_name=sitter.name,
        parent_name=current_user.name,
        booking_time=new_booking.start_time.strftime(
            "%B %d, %Y at %I:%M %p"
        ),
    )

    notification_service = NotificationService(
        NotificationRepository()
    )
    await notification_service.create_and_send(
        session,
        NotificationCreate(
            user_id=sitter.id,
            notification_type=NotificationType.BOOKING_CREATED,
            title="New Booking Request",
            message=(
                f"{current_user.name} has requested a booking "
                f"for {new_booking.start_time.strftime('%B %d, %Y')}"
            ),
            related_booking_id=new_booking.id,
        ),
    )

    return new_booking


@router.get("/", response_model=list[BookingRead])
async def list_bookings(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    booking_repo: BookingRepository = Depends(get_booking_repository),
):
    """List bookings for the current user."""
    bookings = await booking_repo.get_for_user(
        session, current_user.id, skip, limit
    )
    return bookings


@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    booking_repo: BookingRepository = Depends(get_booking_repository),
):
    """Get a specific booking."""
    booking = await booking_repo.get(session, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Only allow access to own bookings
    if (
        booking.parent_id != current_user.id
        and booking.sitter_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Not authorized")

    return booking


@router.patch("/{booking_id}/accept", response_model=BookingRead)
async def accept_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    booking_repo: BookingRepository = Depends(get_booking_repository),
):
    """Accept a booking (sitter only)."""
    booking = await booking_repo.get(session, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.sitter_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the sitter can accept"
        )

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=400, detail="Booking is not pending"
        )

    updated_booking = await booking_repo.update_status(
        session, booking, BookingStatus.ACCEPTED
    )

    # Send notification to parent
    notification_service = NotificationService(
        NotificationRepository()
    )
    await notification_service.create_and_send(
        session,
        NotificationCreate(
            user_id=booking.parent_id,
            notification_type=NotificationType.BOOKING_ACCEPTED,
            title="Booking Accepted!",
            message=f"{current_user.name} accepted your booking",
            related_booking_id=booking.id,
        ),
    )

    return updated_booking


@router.patch("/{booking_id}/decline", response_model=BookingRead)
async def decline_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    booking_repo: BookingRepository = Depends(get_booking_repository),
):
    """Decline a booking (sitter only)."""
    booking = await booking_repo.get(session, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.sitter_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Only the sitter can decline"
        )

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=400, detail="Booking is not pending"
        )

    updated_booking = await booking_repo.update_status(
        session, booking, BookingStatus.DECLINED
    )

    # Send notification to parent
    notification_service = NotificationService(
        NotificationRepository()
    )
    await notification_service.create_and_send(
        session,
        NotificationCreate(
            user_id=booking.parent_id,
            notification_type=NotificationType.BOOKING_DECLINED,
            title="Booking Declined",
            message=f"{current_user.name} declined your booking",
            related_booking_id=booking.id,
        ),
    )

    return updated_booking


@router.websocket("/ws/bookings")
async def websocket_bookings(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time booking updates."""
    # Authenticate user
    async with local_session() as session:
        try:
            user = await get_user_from_token(token, session)
        except ValueError:
            await websocket.close(code=4001, reason="Invalid token")
            return

        # Connect to manager
        connected = await manager.connect(websocket, user.id)
        if not connected:
            return

        try:
            # Send unread notifications on connect
            repo = NotificationRepository()
            unread = await repo.get_unread_for_user(
                session, user.id, limit=20
            )
            for notification in unread:
                notification_dict = {
                    "id": notification.id,
                    "type": notification.notification_type.value,
                    "title": notification.title,
                    "message": notification.message,
                    "created_at": notification.created_at.isoformat(),
                }
                await websocket.send_text(json.dumps(notification_dict))
        except WebSocketDisconnect:
            manager.disconnect(websocket, user.id)
            return

    # Keep connection alive and handle messages
    try:
        while True:
            data = await websocket.receive_text()

            # Rate limiting
            if not manager.check_rate_limit(user.id):
                await websocket.send_text(
                    json.dumps({"error": "Rate limit exceeded"})
                )
                continue

            # Handle ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
