"""Tests for api.py — endpoints, rate limiter, file validation."""

import io
import time

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from PIL import Image

from api import RateLimiter, SecurityConfig, app, rate_limiter, validate_file

# =============================================================================
# Helpers
# =============================================================================


def make_image_bytes(fmt="PNG", size=(100, 100)):
    """Create a valid image in memory."""
    img = Image.new("RGB", size, color="red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def make_upload_file(filename, content):
    """Create a FastAPI UploadFile for testing."""
    return UploadFile(filename=filename, file=io.BytesIO(content))


@pytest.fixture
def client():
    """FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state between tests."""
    original_rpm = rate_limiter.requests_per_minute
    rate_limiter.requests.clear()
    yield
    rate_limiter.requests_per_minute = original_rpm
    rate_limiter.requests.clear()


# =============================================================================
# RateLimiter
# =============================================================================


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_allows_within_limit(self):
        limiter = RateLimiter(requests_per_minute=5)
        for _ in range(5):
            assert limiter.is_allowed("127.0.0.1")

    def test_blocks_over_limit(self):
        limiter = RateLimiter(requests_per_minute=3)
        for _ in range(3):
            limiter.is_allowed("127.0.0.1")
        assert not limiter.is_allowed("127.0.0.1")

    def test_different_ips_independent(self):
        limiter = RateLimiter(requests_per_minute=2)
        limiter.is_allowed("1.1.1.1")
        limiter.is_allowed("1.1.1.1")
        assert not limiter.is_allowed("1.1.1.1")
        assert limiter.is_allowed("2.2.2.2")

    def test_get_remaining(self):
        limiter = RateLimiter(requests_per_minute=10)
        limiter.is_allowed("127.0.0.1")
        limiter.is_allowed("127.0.0.1")
        assert limiter.get_remaining("127.0.0.1") == 8

    def test_expired_requests_dont_count(self):
        limiter = RateLimiter(requests_per_minute=2)
        limiter.requests["127.0.0.1"] = [time.time() - 120, time.time() - 90]
        assert limiter.is_allowed("127.0.0.1")

    def test_cleanup_stale_entries(self):
        limiter = RateLimiter(requests_per_minute=100)
        limiter._CLEANUP_INTERVAL = 0
        limiter.requests["old_ip"] = [time.time() - 120]
        limiter._last_cleanup = 0
        limiter.is_allowed("new_ip")
        assert "old_ip" not in limiter.requests

    def test_cleanup_keeps_active_ips(self):
        limiter = RateLimiter(requests_per_minute=100)
        limiter._CLEANUP_INTERVAL = 0
        limiter._last_cleanup = 0
        limiter.requests["active_ip"] = [time.time() - 10]
        limiter.requests["stale_ip"] = [time.time() - 120]
        limiter.is_allowed("trigger_ip")
        assert "active_ip" in limiter.requests
        assert "stale_ip" not in limiter.requests


# =============================================================================
# SecurityConfig
# =============================================================================


class TestSecurityConfig:
    """Tests for SecurityConfig defaults."""

    def test_defaults(self):
        config = SecurityConfig()
        assert config.MAX_FILE_SIZE == 10 * 1024 * 1024
        assert config.MAX_BATCH_SIZE == 10
        assert ".jpg" in config.ALLOWED_EXTENSIONS
        assert ".png" in config.ALLOWED_EXTENSIONS
        assert "image/jpeg" in config.ALLOWED_MIME_TYPES


# =============================================================================
# File Validation
# =============================================================================


class TestValidateFile:
    """Tests for validate_file function."""

    def test_valid_png(self):
        content = make_image_bytes("PNG")
        f = make_upload_file("test.png", content)
        validate_file(f, content)

    def test_valid_jpeg(self):
        content = make_image_bytes("JPEG")
        f = make_upload_file("photo.jpg", content)
        validate_file(f, content)

    def test_valid_bmp(self):
        content = make_image_bytes("BMP")
        f = make_upload_file("image.bmp", content)
        validate_file(f, content)

    def test_reject_wrong_extension(self):
        content = make_image_bytes("PNG")
        f = make_upload_file("virus.exe", content)
        with pytest.raises(HTTPException) as exc:
            validate_file(f, content)
        assert exc.value.status_code == 400

    def test_reject_oversized(self):
        content = b"x" * (10 * 1024 * 1024 + 1)
        f = make_upload_file("big.png", content)
        with pytest.raises(HTTPException) as exc:
            validate_file(f, content)
        assert exc.value.status_code == 413

    def test_reject_non_image_content(self):
        content = b"this is definitely not an image file at all"
        f = make_upload_file("fake.png", content)
        with pytest.raises(HTTPException) as exc:
            validate_file(f, content)
        assert exc.value.status_code == 400

    def test_no_filename_skips_extension_check(self):
        content = make_image_bytes("PNG")
        f = make_upload_file(None, content)
        validate_file(f, content)


# =============================================================================
# API Endpoints (no model required)
# =============================================================================


class TestEndpointsNoModel:
    """Endpoints that don't require model loading."""

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["message"] == "ChatVLMLLM API"
        assert data["version"] == "1.0.0"
        assert "docs" in data

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "gpu_available" in data
        assert "models_loaded" in data
        assert isinstance(data["loaded_models"], list)

    def test_unload_nonexistent(self, client):
        r = client.delete("/models/nonexistent_model")
        assert r.status_code == 404

    def test_ocr_missing_file(self, client):
        r = client.post("/ocr")
        assert r.status_code == 422

    def test_ocr_invalid_extension(self, client):
        content = make_image_bytes("PNG")
        r = client.post("/ocr", files={"file": ("test.txt", content, "image/png")})
        assert r.status_code == 400

    def test_ocr_non_image(self, client):
        r = client.post(
            "/ocr",
            files={"file": ("test.png", b"not an image", "image/png")},
        )
        assert r.status_code == 400

    def test_batch_too_many(self, client):
        img = make_image_bytes("PNG")
        files = [("files", (f"img_{i}.png", img, "image/png")) for i in range(15)]
        r = client.post("/batch/ocr", files=files)
        assert r.status_code == 400


# =============================================================================
# Rate Limiting on Endpoints
# =============================================================================


class TestEndpointRateLimiting:
    """Test rate limiting on protected endpoints."""

    def test_ocr_rate_limited(self, client):
        rate_limiter.requests_per_minute = 2
        img = make_image_bytes("PNG")

        for _ in range(2):
            client.post("/ocr", files={"file": ("t.png", img, "image/png")})

        r = client.post("/ocr", files={"file": ("t.png", img, "image/png")})
        assert r.status_code == 429

    def test_health_not_rate_limited(self, client):
        rate_limiter.requests_per_minute = 1
        client.get("/health")
        client.get("/health")
        r = client.get("/health")
        assert r.status_code == 200
