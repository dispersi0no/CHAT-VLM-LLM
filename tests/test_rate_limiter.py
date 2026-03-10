"""Unit and integration tests for RateLimiter and rate_limit_check."""

import io
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api import RateLimiter, app, rate_limiter

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_image_bytes(fmt: str = "PNG", size: tuple = (50, 50)) -> bytes:
    img = Image.new("RGB", size, color="blue")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    original_rpm = rate_limiter.requests_per_minute
    rate_limiter.requests.clear()
    rate_limiter._last_cleanup = time.time()
    yield
    rate_limiter.requests_per_minute = original_rpm
    rate_limiter.requests.clear()


# =============================================================================
# TestRateLimiterUnit
# =============================================================================


class TestRateLimiterUnit:
    """Unit tests for the RateLimiter class."""

    def test_first_request_allowed(self):
        limiter = RateLimiter(requests_per_minute=5)
        assert limiter.is_allowed("10.0.0.1") is True

    def test_requests_within_limit_allowed(self):
        limiter = RateLimiter(requests_per_minute=5)
        for _ in range(5):
            assert limiter.is_allowed("10.0.0.2") is True

    def test_request_over_limit_blocked(self):
        limiter = RateLimiter(requests_per_minute=5)
        for _ in range(5):
            limiter.is_allowed("10.0.0.3")
        assert limiter.is_allowed("10.0.0.3") is False

    def test_get_remaining_decrements(self):
        limiter = RateLimiter(requests_per_minute=10)
        limiter.is_allowed("10.0.0.4")
        limiter.is_allowed("10.0.0.4")
        limiter.is_allowed("10.0.0.4")
        assert limiter.get_remaining("10.0.0.4") == 7

    def test_get_remaining_zero_when_exhausted(self):
        limiter = RateLimiter(requests_per_minute=3)
        for _ in range(3):
            limiter.is_allowed("10.0.0.5")
        assert limiter.get_remaining("10.0.0.5") == 0

    def test_different_ips_independent(self):
        limiter = RateLimiter(requests_per_minute=2)
        limiter.is_allowed("10.0.1.1")
        limiter.is_allowed("10.0.1.1")
        assert limiter.is_allowed("10.0.1.1") is False
        assert limiter.is_allowed("10.0.1.2") is True

    def test_old_timestamps_expire(self):
        limiter = RateLimiter(requests_per_minute=2)
        # Populate with timestamps older than the 60-second window
        limiter.requests["1.2.3.4"] = [time.time() - 120, time.time() - 90]
        assert limiter.is_allowed("1.2.3.4") is True

    def test_cleanup_runs_after_interval(self):
        limiter = RateLimiter(requests_per_minute=100)
        # Force cleanup to trigger on the very next is_allowed call
        limiter._CLEANUP_INTERVAL = 0
        limiter._last_cleanup = 0
        # Add a stale IP entry (older than 60 s)
        limiter.requests["stale_ip"] = [time.time() - 120]
        # Trigger cleanup via a fresh request from a different IP
        limiter.is_allowed("trigger_ip")
        assert "stale_ip" not in limiter.requests


# =============================================================================
# TestRateLimitEndpoint
# =============================================================================


class TestRateLimitEndpoint:
    """Integration tests for rate-limiting behaviour via TestClient."""

    def test_health_not_rate_limited(self):
        rate_limiter.requests_per_minute = 1
        # Exhaust a hypothetical limit – /health has no rate_limit_check dependency
        for _ in range(5):
            r = client.get("/health")
            assert r.status_code == 200

    def test_ocr_429_when_limit_exceeded(self):
        img = make_image_bytes("PNG")
        with patch("api.rate_limiter.is_allowed", return_value=False):
            r = client.post(
                "/ocr",
                files={"file": ("test.png", img, "image/png")},
            )
        assert r.status_code == 429

    def test_429_response_has_header(self):
        img = make_image_bytes("PNG")
        with (
            patch("api.rate_limiter.is_allowed", return_value=False),
            patch("api.rate_limiter.get_remaining", return_value=0),
        ):
            r = client.post(
                "/ocr",
                files={"file": ("test.png", img, "image/png")},
            )
        assert r.status_code == 429
        assert r.headers.get("x-ratelimit-remaining") == "0"

    def test_rate_limit_remaining_header_on_success(self):
        img = make_image_bytes("JPEG")
        mock_model_instance = MagicMock()
        mock_model_instance.run.return_value = "some text"
        with patch("api.get_model", return_value=mock_model_instance):
            r = client.post(
                "/ocr",
                files={"file": ("doc.jpg", img, "image/jpeg")},
            )
        assert r.status_code == 200
        assert "x-ratelimit-remaining" in r.headers
