from fastapi.testclient import TestClient


class TestSlowAPILimiter:
    """Tests for SlowAPI rate limiter integration."""

    def test_request_allowed(self, rate_limited_client):
        """Test request is allowed within limit."""
        response = rate_limited_client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"message": "ok"}

    def test_rate_limit_headers(self, rate_limited_client):
        """Test rate limit headers are included."""
        response = rate_limited_client.get("/test")
        assert response.status_code == 200
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers
        assert "x-ratelimit-reset" in response.headers

    def test_rate_limit_exceeded(self, rate_limited_client):
        """Test rate limit exceeded returns 429."""
        # First two requests allowed
        response1 = rate_limited_client.get("/test")
        assert response1.status_code == 200

        response2 = rate_limited_client.get("/test")
        assert response2.status_code == 200

        # Third request should be blocked
        response3 = rate_limited_client.get("/test")
        assert response3.status_code == 429
        assert "Rate limit exceeded" in response3.json()["detail"]

    def test_rate_limit_remaining_decrements(
        self, rate_limited_client
    ):
        """Test remaining count decrements."""
        response1 = rate_limited_client.get("/test")
        remaining1 = int(
            response1.headers["x-ratelimit-remaining"]
        )

        response2 = rate_limited_client.get("/test")
        remaining2 = int(
            response2.headers["x-ratelimit-remaining"]
        )

        assert remaining2 < remaining1

    def test_unlimited_endpoint_not_affected(
        self, rate_limited_client
    ):
        """Test unlimited endpoint is not rate limited."""
        # Exhaust rate limit on /test
        for _ in range(3):
            rate_limited_client.get("/test")

        # Unlimited endpoint should still work
        response = rate_limited_client.get("/unlimited")
        assert response.status_code == 200


class TestSlowAPIClientIsolation:
    """Tests for client isolation in rate limiting."""

    def test_x_forwarded_for_isolation(self, app_with_limiter):
        """Test different clients are isolated."""
        with TestClient(app_with_limiter) as client:
            # Exhaust rate limit for client 1.2.3.4
            for _ in range(2):
                client.get(
                    "/test",
                    headers={"X-Forwarded-For": "1.2.3.4"},
                )

            # Client 1.2.3.4 should be blocked
            response1 = client.get(
                "/test",
                headers={"X-Forwarded-For": "1.2.3.4"},
            )
            assert response1.status_code == 429

            # Client 5.6.7.8 should still work
            response2 = client.get(
                "/test",
                headers={"X-Forwarded-For": "5.6.7.8"},
            )
            assert response2.status_code == 200
