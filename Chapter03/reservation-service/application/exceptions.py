class UsecaseException(Exception):
    """Base exception for application layer errors"""

    pass


class SlotNotFoundException(UsecaseException):
    """Raised when a slot is not found"""

    pass


class InvalidInputException(UsecaseException):
    """Raised when input validation fails"""

    pass
