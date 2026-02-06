import time

import pytest

from middleware.rate_limiter import (
    RateLimiter,
    RateLimitRule,
    TokenBucket,
)


class TestRateLimitRule:
    """Tests for RateLimitRule dataclass."""

    def test_default_burst_size(self):
        """Test burst_size defaults to requests_per_minute."""
        rule = RateLimitRule(requests_per_minute=100)
        assert rule.burst_size == 100

    def test_custom_burst_size(self):
        """Test custom burst_size is preserved."""
        rule = RateLimitRule(
            requests_per_minute=100, burst_size=150
        )
        assert rule.burst_size == 150

    def test_burst_size_can_be_lower(self):
        """Test burst_size can be lower than requests_per_minute."""
        rule = RateLimitRule(
            requests_per_minute=100, burst_size=50
        )
        assert rule.burst_size == 50


class TestTokenBucket:
    """Tests for TokenBucket algorithm."""

    def test_initial_tokens(self):
        """Test bucket starts full."""
        bucket = TokenBucket(capacity=10)
        assert bucket.tokens == 10.0

    def test_refill_rate_calculation(self):
        """Test refill rate is tokens per second."""
        bucket = TokenBucket(capacity=60)
        assert bucket.refill_rate == 1.0

    def test_consume_success(self):
        """Test successful token consumption."""
        bucket = TokenBucket(capacity=10)
        assert bucket.consume() is True
        assert bucket.tokens == 9.0

    def test_consume_empty_bucket(self):
        """Test consumption fails when empty."""
        bucket = TokenBucket(capacity=2)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False

    def test_token_refill_over_time(self):
        """Test tokens refill over time."""
        bucket = TokenBucket(capacity=60)

        # Consume all tokens
        for _ in range(60):
            bucket.consume()

        assert bucket.tokens < 1

        # Simulate time passing
        bucket.last_update = time.time() - 2

        # Next consume should refill ~2 tokens first
        assert bucket.consume() is True

    def test_tokens_capped_at_capacity(self):
        """Test tokens don't exceed capacity after refill."""
        bucket = TokenBucket(capacity=10)

        # Simulate long time passing
        bucket.last_update = time.time() - 1000

        # Consume triggers refill
        bucket.consume()

        # Tokens should be capped at capacity - 1
        assert bucket.tokens <= 9.0

    def test_time_until_available_when_available(self):
        """Test time_until_available returns 0 when tokens available."""
        bucket = TokenBucket(capacity=10)
        assert bucket.time_until_available() == 0

    def test_time_until_available_when_empty(self):
        """Test time_until_available returns positive when empty."""
        bucket = TokenBucket(capacity=60)

        # Drain the bucket
        for _ in range(60):
            bucket.consume()

        wait_time = bucket.time_until_available()
        assert wait_time > 0
        assert wait_time <= 1


class TestRateLimiter:
    """Tests for RateLimiter class."""

    @pytest.fixture
    def rate_limiter(self):
        return RateLimiter()

    def test_no_rules_allows_all(self, rate_limiter):
        """Test requests allowed when no rules match."""
        allowed, headers = rate_limiter.is_allowed(
            "client1", "/any/path"
        )
        assert allowed is True
        assert headers == {}

    def test_add_rule(self, rate_limiter):
        """Test adding a rate limit rule."""
        rate_limiter.add_rule(
            path_matcher=lambda p: p.startswith("/api"),
            requests_per_minute=10,
        )
        assert len(rate_limiter.rules) == 1

    def test_get_rule_matching(self, rate_limiter):
        """Test getting matching rule."""
        rate_limiter.add_rule(
            path_matcher=lambda p: p.startswith("/api"),
            requests_per_minute=10,
        )

        rule = rate_limiter.get_rule("/api/users")
        assert rule is not None
        assert rule.requests_per_minute == 10

    def test_get_rule_no_match(self, rate_limiter):
        """Test getting rule when none match."""
        rate_limiter.add_rule(
            path_matcher=lambda p: p.startswith("/api"),
            requests_per_minute=10,
        )

        rule = rate_limiter.get_rule("/other/path")
        assert rule is None

    def test_first_rule_wins(self, rate_limiter):
        """Test first matching rule is used."""
        rate_limiter.add_rule(
            path_matcher=lambda p: p.startswith("/api"),
            requests_per_minute=10,
        )
        rate_limiter.add_rule(
            path_matcher=lambda p: p.startswith("/api/special"),
            requests_per_minute=100,
        )

        rule = rate_limiter.get_rule("/api/special")
        assert rule.requests_per_minute == 10

    def test_is_allowed_with_rule(self, rate_limiter):
        """Test is_allowed with matching rule."""
        rate_limiter.add_rule(
            path_matcher=lambda p: p.startswith("/api"),
            requests_per_minute=60,
        )

        allowed, headers = rate_limiter.is_allowed(
            "client1", "/api/test"
        )
        assert allowed is True
        assert "X-RateLimit-Limit" in headers
        assert headers["X-RateLimit-Limit"] == "60"

    def test_rate_limit_headers(self, rate_limiter):
        """Test rate limit headers are included."""
        rate_limiter.add_rule(
            path_matcher=lambda p: True,
            requests_per_minute=10,
        )

        allowed, headers = rate_limiter.is_allowed(
            "client1", "/test"
        )

        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

    def test_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit exceeded response."""
        rate_limiter.add_rule(
            path_matcher=lambda p: True,
            requests_per_minute=2,
            burst_size=2,
        )

        # First two requests allowed
        allowed1, _ = rate_limiter.is_allowed("client1", "/test")
        allowed2, _ = rate_limiter.is_allowed("client1", "/test")
        assert allowed1 is True
        assert allowed2 is True

        # Third request blocked
        allowed3, headers = rate_limiter.is_allowed(
            "client1", "/test"
        )
        assert allowed3 is False
        assert "Retry-After" in headers

    def test_per_client_isolation(self, rate_limiter):
        """Test each client has separate rate limits."""
        rate_limiter.add_rule(
            path_matcher=lambda p: True,
            requests_per_minute=2,
            burst_size=2,
        )

        # Exhaust client1's limit
        rate_limiter.is_allowed("client1", "/test")
        rate_limiter.is_allowed("client1", "/test")
        allowed_c1, _ = rate_limiter.is_allowed(
            "client1", "/test"
        )
        assert allowed_c1 is False

        # client2 should still have quota
        allowed_c2, _ = rate_limiter.is_allowed(
            "client2", "/test"
        )
        assert allowed_c2 is True

    def test_pattern_key_uuid_normalization(self, rate_limiter):
        """Test UUID paths are normalized to wildcard."""
        pattern1 = rate_limiter._get_pattern_key(
            "/api/slots/550e8400-e29b-41d4-a716-446655440000"
        )
        pattern2 = rate_limiter._get_pattern_key(
            "/api/slots/123e4567-e89b-12d3-a456-426614174000"
        )

        assert pattern1 == pattern2
        assert "*" in pattern1

    def test_pattern_key_numeric_normalization(
        self, rate_limiter
    ):
        """Test numeric IDs are normalized to wildcard."""
        pattern1 = rate_limiter._get_pattern_key("/api/users/123")
        pattern2 = rate_limiter._get_pattern_key("/api/users/456")

        assert pattern1 == pattern2
        assert "*" in pattern1

    def test_pattern_key_preserves_non_ids(self, rate_limiter):
        """Test non-ID path parts are preserved."""
        pattern = rate_limiter._get_pattern_key(
            "/api/users/profile"
        )
        assert pattern == "/api/users/profile"

    def test_looks_like_id_uuid(self, rate_limiter):
        """Test UUID detection."""
        assert (
            rate_limiter._looks_like_id(
                "550e8400-e29b-41d4-a716-446655440000"
            )
            is True
        )

    def test_looks_like_id_numeric(self, rate_limiter):
        """Test numeric ID detection."""
        assert rate_limiter._looks_like_id("12345") is True

    def test_looks_like_id_text(self, rate_limiter):
        """Test non-ID text detection."""
        assert rate_limiter._looks_like_id("profile") is False
        assert rate_limiter._looks_like_id("users") is False

    def test_looks_like_id_empty(self, rate_limiter):
        """Test empty string is not an ID."""
        assert rate_limiter._looks_like_id("") is False
