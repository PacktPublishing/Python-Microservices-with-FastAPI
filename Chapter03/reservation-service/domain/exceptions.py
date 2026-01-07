class DomainException(Exception):
    """Base exception for domain errors"""

    pass


class SlotNotAvailableException(DomainException):
    """Raised when trying to reserve a slot that's not available"""

    pass


class SlotNotReservedException(DomainException):
    """Raised when trying to confirm/refuse a slot that's not reserved"""

    pass
