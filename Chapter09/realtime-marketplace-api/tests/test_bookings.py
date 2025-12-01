from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from domain.bookings.repositories import BookingRepository
from domain.bookings.schemas import BookingCreate
from domain.bookings.types import BookingStatus
from domain.user.models import User


async def test_create_booking(
    sqlite_session: AsyncSession,
    test_parent: User,
    test_sitter: User,
):
    """Test creating a booking."""
    repo = BookingRepository()
    start = datetime.now(UTC) + timedelta(days=1)
    end = start + timedelta(hours=4)

    booking_data = BookingCreate(
        sitter_id=test_sitter.id,
        start_time=start,
        end_time=end,
        hourly_rate=25.0,
        notes="Test booking",
    )

    booking = await repo.create(
        sqlite_session, booking_data, test_parent.id
    )

    assert booking.id is not None
    assert booking.parent_id == test_parent.id
    assert booking.sitter_id == test_sitter.id
    assert booking.status == BookingStatus.PENDING


async def test_get_booking(
    sqlite_session: AsyncSession,
    test_parent: User,
    test_sitter: User,
):
    """Test getting a booking by ID."""
    repo = BookingRepository()
    start = datetime.now(UTC) + timedelta(days=1)
    end = start + timedelta(hours=4)

    booking = await repo.create(
        sqlite_session,
        BookingCreate(
            sitter_id=test_sitter.id,
            start_time=start,
            end_time=end,
        ),
        test_parent.id,
    )

    found = await repo.get(sqlite_session, booking.id)

    assert found is not None
    assert found.id == booking.id


async def test_get_bookings_for_user(
    sqlite_session: AsyncSession,
    test_parent: User,
    test_sitter: User,
):
    """Test getting bookings for a user."""
    repo = BookingRepository()
    start = datetime.now(UTC) + timedelta(days=1)
    end = start + timedelta(hours=4)

    for _ in range(3):
        await repo.create(
            sqlite_session,
            BookingCreate(
                sitter_id=test_sitter.id,
                start_time=start,
                end_time=end,
            ),
            test_parent.id,
        )

    parent_bookings = await repo.get_for_user(
        sqlite_session, test_parent.id
    )
    sitter_bookings = await repo.get_for_user(
        sqlite_session, test_sitter.id
    )

    assert len(parent_bookings) == 3
    assert len(sitter_bookings) == 3


async def test_update_booking_status(
    sqlite_session: AsyncSession,
    test_parent: User,
    test_sitter: User,
):
    """Test updating booking status."""
    repo = BookingRepository()
    start = datetime.now(UTC) + timedelta(days=1)
    end = start + timedelta(hours=4)

    booking = await repo.create(
        sqlite_session,
        BookingCreate(
            sitter_id=test_sitter.id,
            start_time=start,
            end_time=end,
        ),
        test_parent.id,
    )

    updated = await repo.update_status(
        sqlite_session, booking, BookingStatus.ACCEPTED
    )

    assert updated.status == BookingStatus.ACCEPTED


async def test_booking_endpoint_queues_emails(
    client, test_parent, test_sitter, parent_token, celery_config
):
    """Test that creating booking queues email tasks."""
    start = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    end = (datetime.now(UTC) + timedelta(days=1, hours=4)).isoformat()

    with patch(
        "domain.bookings.views.send_booking_confirmation_to_parent"
    ) as mock_parent_email, patch(
        "domain.bookings.views.send_booking_notification_to_sitter"
    ) as mock_sitter_email:
        response = await client.post(
            "/bookings/",
            json={
                "sitter_id": test_sitter.id,
                "start_time": start,
                "end_time": end,
            },
            headers={"Authorization": f"Bearer {parent_token}"},
        )

        assert response.status_code == 201

        mock_parent_email.delay.assert_called_once()
        mock_sitter_email.delay.assert_called_once()

        parent_call_kwargs = mock_parent_email.delay.call_args.kwargs
        assert parent_call_kwargs["parent_email"] == test_parent.email
        assert parent_call_kwargs["parent_name"] == test_parent.name
        assert parent_call_kwargs["sitter_name"] == test_sitter.name

        sitter_call_kwargs = mock_sitter_email.delay.call_args.kwargs
        assert sitter_call_kwargs["sitter_email"] == test_sitter.email
        assert sitter_call_kwargs["sitter_name"] == test_sitter.name
        assert sitter_call_kwargs["parent_name"] == test_parent.name


async def test_booking_validation_end_after_start(
    client, test_parent, test_sitter, parent_token
):
    """Test that end_time must be after start_time."""
    start = datetime.now(UTC) + timedelta(days=1)
    end = start - timedelta(hours=1)

    response = await client.post(
        "/bookings/",
        json={
            "sitter_id": test_sitter.id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers={"Authorization": f"Bearer {parent_token}"},
    )

    assert response.status_code == 422
