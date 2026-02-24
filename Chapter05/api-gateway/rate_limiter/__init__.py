from fastapi.requests import Request
from slowapi import Limiter


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.

    Checks X-Forwarded-For header first (for proxy scenarios),
    then falls back to direct client IP.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


# Create limiter instance with IP-based rate limiting
limiter = Limiter(
    key_func=get_client_ip,
    headers_enabled=True,
    default_limits=["60/minute"],
)
