"""Tests for API security hardening (PR #96).

Covers security headers, model allowlist, error masking, file validation,
batch limits, and the health endpoint using FastAPI TestClient.
"""

import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from api import ALLOWED_MODELS, app, model_cache, rate_limiter

client = TestClient(app)


# =============================================================================
# Helpers
# =============================================================================


def _make_test_image() -> io.BytesIO:
    """Return a small valid PNG image as a BytesIO buffer."""
    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset shared mutable state (model cache, rate limiter) between tests."""
    model_cache.clear()
    rate_limiter.requests.clear()
    yield
    model_cache.clear()
    rate_limiter.requests.clear()


# =============================================================================
# TestSecurityHeaders
# =============================================================================


class TestSecurityHeaders:
    """Security headers must be present on every response."""

    def test_security_headers_on_root(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["x-frame-options"] == "DENY"
        assert r.headers["x-xss-protection"] == "1; mode=block"
        assert "referrer-policy" in r.headers
        assert "permissions-policy" in r.headers

    def test_security_headers_on_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["x-frame-options"] == "DENY"
        assert r.headers["x-xss-protection"] == "1; mode=block"
        assert "referrer-policy" in r.headers
        assert "permissions-policy" in r.headers

    def test_security_headers_on_error(self):
        # A 404 error response should still carry security headers.
        r = client.delete("/models/nonexistent")
        assert r.status_code == 404
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["x-frame-options"] == "DENY"
        assert r.headers["x-xss-protection"] == "1; mode=block"
        assert "referrer-policy" in r.headers
        assert "permissions-policy" in r.headers


# =============================================================================
# TestModelAllowlist
# =============================================================================


class TestModelAllowlist:
    """Unknown / injected model names must be rejected with a 400."""

    def test_unknown_model_rejected(self):
        buf = _make_test_image()
        r = client.post(
            "/ocr",
            files={"file": ("test.png", buf, "image/png")},
            params={"model": "evil_injection"},
        )
        assert r.status_code == 400

    def test_error_lists_available_models(self):
        buf = _make_test_image()
        r = client.post(
            "/ocr",
            files={"file": ("test.png", buf, "image/png")},
            params={"model": "evil_injection"},
        )
        detail = r.json()["detail"]
        assert any(model in detail for model in ALLOWED_MODELS)

    def test_models_endpoint_returns_allowed(self):
        r = client.get("/models")
        assert r.status_code == 200
        available = r.json()["available"]
        assert all(model in available for model in ALLOWED_MODELS)


# =============================================================================
# TestErrorMasking
# =============================================================================


class TestErrorMasking:
    """Internal errors must not leak implementation details to clients."""

    def test_internal_error_not_leaked(self):
        buf = _make_test_image()
        with patch("api.get_model") as mock_get:
            mock_get.side_effect = Exception(
                "GPU out of memory: detailed traceback info"
            )
            r = client.post(
                "/ocr",
                files={"file": ("test.png", buf, "image/png")},
                params={"model": "got_ocr"},
            )
        assert r.status_code == 500
        body = r.text
        assert "traceback" not in body.lower()
        assert "GPU out of memory" not in body
        assert "detailed" not in body

    def test_unload_nonexistent_404(self):
        r = client.delete("/models/nonexistent")
        assert r.status_code == 404


# =============================================================================
# TestFileValidation
# =============================================================================


class TestFileValidation:
    """Uploaded files must be validated for size, extension, and content."""

    def test_oversized_file_rejected(self):
        # 11 MB exceeds the 10 MB limit → 413
        content = b"x" * (11 * 1024 * 1024)
        r = client.post(
            "/ocr",
            files={"file": ("big.png", content, "image/png")},
        )
        assert r.status_code == 413

    def test_non_image_rejected(self):
        # PE/EXE magic bytes with .exe extension → 400
        content = b"\x4d\x5a\x90\x00" + b"\x00" * 100
        r = client.post(
            "/ocr",
            files={"file": ("malware.exe", content, "image/png")},
        )
        assert r.status_code == 400

    def test_invalid_extension_rejected(self):
        buf = _make_test_image()
        r = client.post(
            "/ocr",
            files={"file": ("script.py", buf, "image/png")},
        )
        assert r.status_code == 400


# =============================================================================
# TestBatchLimits
# =============================================================================


class TestBatchLimits:
    """Batch endpoint must reject requests that exceed the file count limit."""

    def test_batch_over_10_files_rejected(self):
        content = _make_test_image().read()
        files = [("files", (f"img_{i}.png", content, "image/png")) for i in range(11)]
        r = client.post("/batch/ocr", files=files)
        assert r.status_code == 400


# =============================================================================
# TestHealthEndpoint
# =============================================================================


class TestHealthEndpoint:
    """Health endpoint must return the expected fields."""

    def test_health_200(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "gpu_available" in data
        assert "rate_limit_per_minute" in data
