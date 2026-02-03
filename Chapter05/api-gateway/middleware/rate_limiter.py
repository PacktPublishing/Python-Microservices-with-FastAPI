import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass
class RateLimitRule:
    requests_per_minute: int
    burst_size: int | None = None  # Optional burst allowance

    def __post_init__(self):
        if self.burst_size is None:
            self.burst_size = self.requests_per_minute


@dataclass
class TokenBucket:
    capacity: int
    tokens: float = field(default=0)
    last_update: float = field(default_factory=time.time)
    refill_rate: float = field(default=0)  # tokens per second

    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.refill_rate = self.capacity / 60.0  # Convert from per-minute to per-second

    def consume(self) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # Refill tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    def time_until_available(self) -> float:
        if self.tokens >= 1:
            return 0
        tokens_needed = 1 - self.tokens
        return tokens_needed / self.refill_rate


class RateLimiter:
    def __init__(self):
        # Client buckets: client_id -> path_pattern -> TokenBucket
        self.buckets: dict[str, dict[str, TokenBucket]] = defaultdict(dict)
        self.rules: list[tuple[Callable[[str], bool], RateLimitRule]] = []

    def add_rule(
        self,
        path_matcher: Callable[[str], bool],
        requests_per_minute: int,
        burst_size: int | None = None,
    ):
        """Add a rate limiting rule for paths matching the given function."""
        rule = RateLimitRule(
            requests_per_minute=requests_per_minute,
            burst_size=burst_size,
        )
        self.rules.append((path_matcher, rule))

    def get_rule(self, path: str) -> RateLimitRule | None:
        """Find the first matching rule for a path."""
        for matcher, rule in self.rules:
            if matcher(path):
                return rule
        return None

    def is_allowed(self, client_id: str, path: str) -> tuple[bool, dict]:
        """
        Check if a request is allowed under rate limiting.

        Returns:
            tuple: (allowed: bool, headers: dict with rate limit info)
        """
        rule = self.get_rule(path)
        if rule is None:
            # No rate limit rule for this path
            return True, {}

        # Get or create bucket for this client and path pattern
        pattern_key = self._get_pattern_key(path)
        if pattern_key not in self.buckets[client_id]:
            self.buckets[client_id][pattern_key] = TokenBucket(
                capacity=rule.burst_size or rule.requests_per_minute,
            )

        bucket = self.buckets[client_id][pattern_key]
        allowed = bucket.consume()

        headers = {
            "X-RateLimit-Limit": str(rule.requests_per_minute),
            "X-RateLimit-Remaining": str(int(bucket.tokens)),
            "X-RateLimit-Reset": str(int(time.time() + 60)),
        }

        if not allowed:
            retry_after = bucket.time_until_available()
            headers["Retry-After"] = str(int(retry_after) + 1)

        return allowed, headers

    def _get_pattern_key(self, path: str) -> str:
        """Convert a path to a pattern key for bucket grouping."""
        # Group similar paths together (e.g., /reservations/slots/123 -> /reservations/slots/*)
        parts = path.split("/")
        normalized = []
        for part in parts:
            # Replace UUIDs and numeric IDs with wildcards
            if self._looks_like_id(part):
                normalized.append("*")
            else:
                normalized.append(part)
        return "/".join(normalized)

    def _looks_like_id(self, part: str) -> bool:
        """Check if a path part looks like an ID (UUID or numeric)."""
        if not part:
            return False
        # Check for UUID format
        if len(part) == 36 and part.count("-") == 4:
            return True
        # Check for numeric ID
        if part.isdigit():
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next) -> Response:
        # Use client IP as identifier (in production, consider using API keys)
        client_id = self._get_client_id(request)
        path = request.url.path

        allowed, headers = self.rate_limiter.is_allowed(client_id, path)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": headers.get("Retry-After"),
                },
                headers=headers,
            )

        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response

    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Check for X-Forwarded-For header (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"
