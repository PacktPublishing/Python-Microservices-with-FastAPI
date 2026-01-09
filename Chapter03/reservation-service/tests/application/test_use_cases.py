import pytest
from decimal import Decimal
from uuid import uuid4

from application.use_cases import (
    CreateAvailabilitySlotUseCase,
    ReserveSlotUseCase,
    ConfirmReservationUseCase,
    RefuseReservationUseCase,
    ListAvailableSlotsUseCase,
)
from application.dtos import (
    CreateSlotRequest,
    ReserveSlotRequest,
    ConfirmSlotRequest,
    RefuseSlotRequest,
    ListAvailableSlotsRequest,
)
from application.exceptions import (
    InvalidInputException,
    SlotNotFoundException,
)
from domain.value_objects import WeekDay, TimeSlot, BabysitterInfo
from domain.entities import AvailabilitySlot


class TestCreateAvailabilitySlotUseCase:
    def test_create_slot_successfully(self, empty_repository):
        use_case = CreateAvailabilitySlotUseCase(empty_repository)

        request = CreateSlotRequest(
            week_day=WeekDay.MONDAY,
            time_slot=TimeSlot.MORNING,
            babysitter_name="Maria Rodriguez",
        )

        response = use_case.execute(request)

        assert response.week_day.value == "monday"
        assert response.time_slot.value == "morning"
        assert response.babysitter_name == "Maria Rodriguez"
        assert response.status == "available"
        assert response.id is not None

    def test_create_slot_persists_to_repository(
        self, empty_repository
    ):
        use_case = CreateAvailabilitySlotUseCase(empty_repository)

        request = CreateSlotRequest(
            week_day=WeekDay.TUESDAY,
            time_slot=TimeSlot.AFTERNOON,
            babysitter_name="Sophie Dubois",
        )

        response = use_case.execute(request)

        # Verify it's in the repository
        slot = empty_repository.find_by_id(response.id)
        assert slot is not None
        assert slot.babysitter.name == "Sophie Dubois"

    def test_create_slot_with_invalid_week_day(
        self, empty_repository
    ):
        use_case = CreateAvailabilitySlotUseCase(empty_repository)

        request = CreateSlotRequest(
            week_day="funday",  # ty: ignore[invalid-argument-type]
            time_slot=TimeSlot.MORNING,
            babysitter_name="Maria",
        )

        with pytest.raises(
            InvalidInputException, match="Invalid input"
        ):
            use_case.execute(request)

    def test_create_slot_with_empty_babysitter_name(
        self, empty_repository
    ):
        use_case = CreateAvailabilitySlotUseCase(empty_repository)

        request = CreateSlotRequest(
            week_day=WeekDay.MONDAY,
            time_slot=TimeSlot.MORNING,
            babysitter_name="",  # Invalid
        )

        with pytest.raises(
            InvalidInputException, match="Invalid input"
        ):
            use_case.execute(request)


class TestReserveSlotUseCase:
    def test_reserve_available_slot_successfully(
        self, empty_repository
    ):
        # Create a slot first
        slot = AvailabilitySlot(
            week_day=WeekDay.MONDAY,
            time_slot=TimeSlot.MORNING,
            babysitter=BabysitterInfo(name="Maria Rodriguez"),
        )
        saved_slot = empty_repository.save(slot)

        # Reserve it
        use_case = ReserveSlotUseCase(empty_repository)
        request = ReserveSlotRequest(
            slot_id=saved_slot.id,
            parent_email="parent@example.com",
            description="Need help with 2 kids",
        )

        response = use_case.execute(request)

        assert response.status == "reserved"
        assert response.reservation_email == "parent@example.com"
        assert (
            response.reservation_description
            == "Need help with 2 kids"
        )
        assert response.reserved_at is not None

    def test_reserve_already_reserved_slot(
        self, empty_repository
    ):
        # Create and reserve a slot
        slot = AvailabilitySlot(
            week_day=WeekDay.MONDAY,
            time_slot=TimeSlot.MORNING,
            babysitter=BabysitterInfo(name="Maria"),
        )
        saved_slot = empty_repository.save(slot)

        use_case = ReserveSlotUseCase(empty_repository)

        # First reservation
        request1 = ReserveSlotRequest(
            slot_id=saved_slot.id,
            parent_email="parent1@example.com",
        )
        use_case.execute(request1)

        # Try to reserve again
        request2 = ReserveSlotRequest(
            slot_id=saved_slot.id,
            parent_email="parent2@example.com",
        )

        with pytest.raises(
            InvalidInputException, match="not available"
        ):
            use_case.execute(request2)

    def test_reserve_non_existent_slot(self, empty_repository):
        use_case = ReserveSlotUseCase(empty_repository)

        request = ReserveSlotRequest(
            slot_id=uuid4(),  # Random UUID that doesn't exist
            parent_email="parent@example.com",
        )

        with pytest.raises(SlotNotFoundException):
            use_case.execute(request)

    def test_reserve_with_invalid_email(self, empty_repository):
        slot = AvailabilitySlot(
            week_day=WeekDay.MONDAY,
            time_slot=TimeSlot.MORNING,
            babysitter=BabysitterInfo(name="Maria"),
        )
        saved_slot = empty_repository.save(slot)

        use_case = ReserveSlotUseCase(empty_repository)

        request = ReserveSlotRequest(
            slot_id=saved_slot.id,
            parent_email="invalidemail.com",
        )

        with pytest.raises(InvalidInputException):
            use_case.execute(request)


class TestConfirmReservationUseCase:
    def test_confirm_reserved_slot_successfully(
        self, empty_repository
    ):
        # Create and reserve a slot
        slot = AvailabilitySlot(
            week_day=WeekDay.MONDAY,
            time_slot=TimeSlot.MORNING,
            babysitter=BabysitterInfo(name="Maria"),
        )
        saved_slot = empty_repository.save(slot)

        # Reserve it
        reserve_use_case = ReserveSlotUseCase(empty_repository)
        reserve_request = ReserveSlotRequest(
            slot_id=saved_slot.id,
            parent_email="parent@example.com",
        )
        reserve_use_case.execute(reserve_request)

        # Confirm it
        confirm_use_case = ConfirmReservationUseCase(
            empty_repository
        )
        confirm_request = ConfirmSlotRequest(
            slot_id=saved_slot.id
        )

        response = confirm_use_case.execute(confirm_request)

        assert response.status == "confirmed"
        assert response.confirmed_at is not None
        assert response.reservation_email == "parent@example.com"

    def test_confirm_non_existent_slot(self, empty_repository):
        use_case = ConfirmReservationUseCase(empty_repository)
        request = ConfirmSlotRequest(slot_id=uuid4())

        with pytest.raises(SlotNotFoundException):
            use_case.execute(request)

    def test_confirm_available_slot_raises_error(
        self, empty_repository
    ):
        # Create an available slot (not reserved)
        slot = AvailabilitySlot(
            week_day=WeekDay.MONDAY,
            time_slot=TimeSlot.MORNING,
            babysitter=BabysitterInfo(name="Maria"),
        )
        saved_slot = empty_repository.save(slot)

        use_case = ConfirmReservationUseCase(empty_repository)
        request = ConfirmSlotRequest(slot_id=saved_slot.id)

        with pytest.raises(
            InvalidInputException, match="not in reserved state"
        ):
            use_case.execute(request)


class TestRefuseReservationUseCase:
    def test_refuse_reserved_slot_successfully(
        self, empty_repository
    ):
        # Create and reserve a slot
        slot = AvailabilitySlot(
            week_day=WeekDay.MONDAY,
            time_slot=TimeSlot.MORNING,
            babysitter=BabysitterInfo(name="Maria"),
        )
        saved_slot = empty_repository.save(slot)

        # Reserve it
        reserve_use_case = ReserveSlotUseCase(empty_repository)
        reserve_request = ReserveSlotRequest(
            slot_id=saved_slot.id,
            parent_email="parent@example.com",
            description="Test reservation",
        )
        reserve_use_case.execute(reserve_request)

        # Refuse it
        refuse_use_case = RefuseReservationUseCase(
            empty_repository
        )
        refuse_request = RefuseSlotRequest(slot_id=saved_slot.id)

        response = refuse_use_case.execute(refuse_request)

        assert response.status == "available"
        assert response.reservation_email is None
        assert response.reservation_description is None
        assert response.reserved_at is None

    def test_refuse_makes_slot_available_again(
        self, empty_repository
    ):
        # Create and reserve a slot
        slot = AvailabilitySlot(
            week_day=WeekDay.MONDAY,
            time_slot=TimeSlot.MORNING,
            babysitter=BabysitterInfo(name="Maria"),
        )
        saved_slot = empty_repository.save(slot)

        # Reserve it
        reserve_use_case = ReserveSlotUseCase(empty_repository)
        reserve_request = ReserveSlotRequest(
            slot_id=saved_slot.id,
            parent_email="parent1@example.com",
        )
        reserve_use_case.execute(reserve_request)

        # Refuse it
        refuse_use_case = RefuseReservationUseCase(
            empty_repository
        )
        refuse_request = RefuseSlotRequest(slot_id=saved_slot.id)
        refuse_use_case.execute(refuse_request)

        # Should be able to reserve again
        new_reserve_request = ReserveSlotRequest(
            slot_id=saved_slot.id,
            parent_email="parent2@example.com",
        )
        response = reserve_use_case.execute(new_reserve_request)

        assert response.status == "reserved"
        assert response.reservation_email == "parent2@example.com"

    def test_refuse_non_existent_slot(self, empty_repository):
        use_case = RefuseReservationUseCase(empty_repository)
        request = RefuseSlotRequest(slot_id=uuid4())

        with pytest.raises(SlotNotFoundException):
            use_case.execute(request)

    def test_refuse_available_slot_raises_error(
        self, empty_repository
    ):
        # Create an available slot (not reserved)
        slot = AvailabilitySlot(
            week_day=WeekDay.MONDAY,
            time_slot=TimeSlot.MORNING,
            babysitter=BabysitterInfo(name="Maria"),
        )
        saved_slot = empty_repository.save(slot)

        use_case = RefuseReservationUseCase(empty_repository)
        request = RefuseSlotRequest(slot_id=saved_slot.id)

        with pytest.raises(
            InvalidInputException, match="not in reserved state"
        ):
            use_case.execute(request)


class TestListAvailableSlotsUseCase:
    def test_list_all_available_slots(self, seeded_repository):
        use_case = ListAvailableSlotsUseCase(seeded_repository)
        request = ListAvailableSlotsRequest()

        response = use_case.execute(request)

        # All 21 seeded slots should be available
        assert len(response) == 21
        assert all(
            slot.status == "available" for slot in response
        )

    def test_list_slots_filtered_by_week_day(
        self, seeded_repository
    ):
        use_case = ListAvailableSlotsUseCase(seeded_repository)
        request = ListAvailableSlotsRequest(
            week_day=WeekDay.MONDAY
        )

        response = use_case.execute(request)

        # Should only return Monday slots (3 time slots)
        assert len(response) == 3
        assert all(
            slot.week_day == WeekDay.MONDAY for slot in response
        )

    def test_list_slots_filtered_by_time_slot(
        self, seeded_repository
    ):
        use_case = ListAvailableSlotsUseCase(seeded_repository)
        request = ListAvailableSlotsRequest(
            time_slot=TimeSlot.MORNING
        )

        response = use_case.execute(request)

        # Should return morning slots for all 7 days
        assert len(response) == 7
        assert all(
            slot.time_slot == TimeSlot.MORNING
            for slot in response
        )

    def test_list_slots_filtered_by_both(self, seeded_repository):
        use_case = ListAvailableSlotsUseCase(seeded_repository)
        request = ListAvailableSlotsRequest(
            week_day=WeekDay.TUESDAY, time_slot=TimeSlot.AFTERNOON
        )

        response = use_case.execute(request)

        # Should return only Tuesday afternoon slot
        assert len(response) == 1
        assert response[0].week_day.value == "tuesday"
        assert response[0].time_slot.value == "afternoon"

    def test_list_empty_repository(self, empty_repository):
        use_case = ListAvailableSlotsUseCase(empty_repository)
        request = ListAvailableSlotsRequest()

        response = use_case.execute(request)

        assert len(response) == 0


class TestUseCaseIntegration:
    """Integration tests for complete workflows"""

    def test_complete_reservation_flow_confirm(
        self, empty_repository
    ):
        """Test: Create -> Reserve -> Confirm"""
        # Create slot
        create_use_case = CreateAvailabilitySlotUseCase(
            empty_repository
        )
        create_request = CreateSlotRequest(
            week_day=WeekDay.FRIDAY,
            time_slot=TimeSlot.NIGHT,
            babysitter_name="Sophie Dubois",
        )
        created_slot = create_use_case.execute(create_request)

        # Reserve slot
        reserve_use_case = ReserveSlotUseCase(empty_repository)
        reserve_request = ReserveSlotRequest(
            slot_id=created_slot.id,
            parent_email="parent@example.com",
            description="Urgent babysitting needed",
        )
        reserved_slot = reserve_use_case.execute(reserve_request)
        assert reserved_slot.status == "reserved"

        # Confirm reservation
        confirm_use_case = ConfirmReservationUseCase(
            empty_repository
        )
        confirm_request = ConfirmSlotRequest(
            slot_id=created_slot.id
        )
        confirmed_slot = confirm_use_case.execute(confirm_request)

        assert confirmed_slot.status == "confirmed"
        assert (
            confirmed_slot.reservation_email
            == "parent@example.com"
        )

    def test_complete_reservation_flow_refuse(
        self, empty_repository
    ):
        """Test: Create -> Reserve -> Refuse -> Reserve again"""
        # Create slot
        create_use_case = CreateAvailabilitySlotUseCase(
            empty_repository
        )
        create_request = CreateSlotRequest(
            week_day=WeekDay.SATURDAY,
            time_slot=TimeSlot.MORNING,
            babysitter_name="Emma Johnson",
        )
        created_slot = create_use_case.execute(create_request)

        # First reservation
        reserve_use_case = ReserveSlotUseCase(empty_repository)
        reserve_request1 = ReserveSlotRequest(
            slot_id=created_slot.id,
            parent_email="parent1@example.com",
        )
        reserve_use_case.execute(reserve_request1)

        # Refuse reservation
        refuse_use_case = RefuseReservationUseCase(
            empty_repository
        )
        refuse_request = RefuseSlotRequest(
            slot_id=created_slot.id
        )
        refused_slot = refuse_use_case.execute(refuse_request)
        assert refused_slot.status == "available"

        # Second reservation (should work now)
        reserve_request2 = ReserveSlotRequest(
            slot_id=created_slot.id,
            parent_email="parent2@example.com",
        )
        new_reservation = reserve_use_case.execute(
            reserve_request2
        )

        assert new_reservation.status == "reserved"
        assert (
            new_reservation.reservation_email
            == "parent2@example.com"
        )
