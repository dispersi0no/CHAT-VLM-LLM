"""Tests for api.py — endpoints, rate limiter, file validation."""

import io
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from PIL import Image

from api import (
    RateLimiter,
    SecurityConfig,
    app,
    model_cache,
    rate_limiter,
    validate_file,
)

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
    """FastAPI TestClient with cleared state."""
    model_cache.clear()
    rate_limiter.requests.clear()
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


# =============================================================================
# SecurityConfig — env parsing
# =============================================================================


class TestSecurityConfigEnv:
    """Tests for SecurityConfig CORS origins env parsing."""

    def test_cors_origins_is_list(self):
        config = SecurityConfig()
        assert isinstance(config.CORS_ORIGINS, list)
        assert len(config.CORS_ORIGINS) >= 1

    def test_cors_origins_default_contains_localhost(self):
        config = SecurityConfig()
        assert any("localhost" in origin for origin in config.CORS_ORIGINS)

    def test_cors_origins_parsed_from_env(self):
        # CORS_ORIGINS is split from a comma-separated env string at class load time
        config = SecurityConfig()
        assert "http://localhost:8501" in config.CORS_ORIGINS
        assert "http://localhost:3000" in config.CORS_ORIGINS
        assert "http://127.0.0.1:8501" in config.CORS_ORIGINS


# =============================================================================
# Models endpoint
# =============================================================================


class TestModelsEndpoint:
    """Tests for GET /models endpoint."""

    def test_list_models_returns_available_and_loaded(self, client):
        import sys

        mock_models = MagicMock()
        mock_models.ModelLoader.get_available_models.return_value = [
            "model_a",
            "model_b",
        ]
        with patch.dict(sys.modules, {"models": mock_models}):
            r = client.get("/models")
        assert r.status_code == 200
        data = r.json()
        assert "available" in data
        assert "loaded" in data
        assert isinstance(data["available"], list)
        assert isinstance(data["loaded"], list)

    def test_list_models_includes_cached(self, client):
        import sys

        model_cache["cached_model"] = MagicMock()
        mock_models = MagicMock()
        mock_models.ModelLoader.get_available_models.return_value = []
        with patch.dict(sys.modules, {"models": mock_models}):
            r = client.get("/models")
        assert "cached_model" in r.json()["loaded"]
        model_cache.clear()


# =============================================================================
# OCR endpoint — with mocked model
# =============================================================================


class TestOCREndpoint:
    """Tests for POST /ocr endpoint."""

    def test_ocr_success(self, client):
        img = make_image_bytes("JPEG")
        mock_model = MagicMock()
        mock_model.run.return_value = "extracted text"
        with patch("api.get_model", return_value=mock_model):
            r = client.post(
                "/ocr",
                files={"file": ("doc.jpg", img, "image/jpeg")},
                params={"model": "test_model"},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["text"] == "extracted text"
        assert data["model"] == "test_model"
        assert "processing_time" in data
        assert "image_size" in data

    def test_ocr_with_language_hint(self, client):
        img = make_image_bytes("PNG")
        mock_model = MagicMock()
        mock_model.run.return_value = "texto extraído"
        with patch("api.get_model", return_value=mock_model):
            r = client.post(
                "/ocr",
                files={"file": ("doc.png", img, "image/png")},
                params={"model": "test_model", "language": "es"},
            )
        assert r.status_code == 200
        assert r.json()["language"] == "es"

    def test_ocr_invalid_extension(self, client):
        img = make_image_bytes("PNG")
        r = client.post("/ocr", files={"file": ("test.txt", img, "image/png")})
        assert r.status_code == 400

    def test_ocr_non_image_content(self, client):
        r = client.post(
            "/ocr",
            files={"file": ("test.png", b"not an image", "image/png")},
        )
        assert r.status_code == 400

    def test_ocr_file_too_large(self, client):
        content = b"x" * (10 * 1024 * 1024 + 1)
        r = client.post("/ocr", files={"file": ("big.png", content, "image/png")})
        assert r.status_code == 413

    def test_ocr_rate_limit_header_present(self, client):
        img = make_image_bytes("JPEG")
        mock_model = MagicMock()
        mock_model.run.return_value = "text"
        with patch("api.get_model", return_value=mock_model):
            r = client.post(
                "/ocr",
                files={"file": ("doc.jpg", img, "image/jpeg")},
            )
        assert "x-ratelimit-remaining" in r.headers


# =============================================================================
# Chat endpoint — with mocked model
# =============================================================================


class TestChatEndpoint:
    """Tests for POST /chat endpoint."""

    def test_chat_success(self, client):
        img = make_image_bytes("JPEG")
        mock_model = MagicMock()
        mock_model.run.return_value = "This is a red square."
        with patch("api.get_model", return_value=mock_model):
            r = client.post(
                "/chat",
                files={"file": ("photo.jpg", img, "image/jpeg")},
                data={"prompt": "What do you see?", "model": "test_model"},
            )
        assert r.status_code == 200
        data = r.json()
        assert data["response"] == "This is a red square."
        assert data["model"] == "test_model"
        assert "processing_time" in data
        assert "prompt" in data

    def test_chat_invalid_extension(self, client):
        img = make_image_bytes("PNG")
        r = client.post(
            "/chat",
            files={"file": ("doc.pdf", img, "image/png")},
            data={"prompt": "describe it"},
        )
        assert r.status_code == 400

    def test_chat_missing_file(self, client):
        r = client.post("/chat", data={"prompt": "hello"})
        assert r.status_code == 422

    def test_chat_rate_limit_header_present(self, client):
        img = make_image_bytes("PNG")
        mock_model = MagicMock()
        mock_model.run.return_value = "answer"
        with patch("api.get_model", return_value=mock_model):
            r = client.post(
                "/chat",
                files={"file": ("img.png", img, "image/png")},
                data={"prompt": "describe"},
            )
        assert "x-ratelimit-remaining" in r.headers


# =============================================================================
# Batch OCR endpoint
# =============================================================================


class TestBatchOCREndpoint:
    """Tests for POST /batch/ocr endpoint."""

    def test_batch_ocr_success(self, client):
        img = make_image_bytes("PNG")
        mock_model = MagicMock()
        mock_model.run.return_value = "page text"
        files = [("files", (f"img_{i}.png", img, "image/png")) for i in range(3)]
        with patch("api.get_model", return_value=mock_model):
            r = client.post("/batch/ocr", files=files)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
        assert data["successful"] == 3
        assert data["failed"] == 0
        assert len(data["results"]) == 3

    def test_batch_exceeds_max_size(self, client):
        img = make_image_bytes("PNG")
        files = [("files", (f"img_{i}.png", img, "image/png")) for i in range(15)]
        r = client.post("/batch/ocr", files=files)
        assert r.status_code == 400

    def test_batch_mixed_valid_invalid(self, client):
        valid_img = make_image_bytes("PNG")
        mock_model = MagicMock()
        mock_model.run.return_value = "text"
        files = [
            ("files", ("valid.png", valid_img, "image/png")),
            ("files", ("bad.exe", b"not an image", "image/png")),
        ]
        with patch("api.get_model", return_value=mock_model):
            r = client.post("/batch/ocr", files=files)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        statuses = {res["filename"]: res["status"] for res in data["results"]}
        assert statuses["valid.png"] == "success"
        assert statuses["bad.exe"] == "error"

    def test_batch_rate_limit_header_present(self, client):
        img = make_image_bytes("PNG")
        mock_model = MagicMock()
        mock_model.run.return_value = "text"
        with patch("api.get_model", return_value=mock_model):
            r = client.post(
                "/batch/ocr",
                files=[("files", ("img.png", img, "image/png"))],
            )
        assert "x-ratelimit-remaining" in r.headers


# =============================================================================
# Unload model endpoint
# =============================================================================


class TestUnloadModelEndpoint:
    """Tests for DELETE /models/{model_name}."""

    def test_unload_loaded_model(self, client):
        mock_model = MagicMock(spec=object)  # base object has no .unload attribute
        model_cache["my_model"] = mock_model
        r = client.delete("/models/my_model")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert "my_model" not in model_cache

    def test_unload_model_calls_unload_method(self, client):
        mock_model = MagicMock()
        mock_model.unload = MagicMock()
        model_cache["unloadable"] = mock_model
        r = client.delete("/models/unloadable")
        assert r.status_code == 200
        mock_model.unload.assert_called_once()

    def test_unload_nonexistent_returns_404(self, client):
        r = client.delete("/models/nonexistent_model")
        assert r.status_code == 404


# =============================================================================
# Exception handlers
# =============================================================================


class TestExceptionHandlers:
    """Tests for custom exception handler response format."""

    def test_http_exception_returns_json_with_status_code(self, client):
        r = client.delete("/models/not_loaded_model")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert "status_code" in data
        assert data["status_code"] == 404

    def test_http_exception_400_format(self, client):
        r = client.post(
            "/ocr",
            files={"file": ("virus.exe", make_image_bytes("PNG"), "image/png")},
        )
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert "status_code" in data
        assert data["status_code"] == 400

    def test_general_exception_returns_500(self, client):
        img = make_image_bytes("JPEG")
        mock_model = MagicMock()
        mock_model.run.side_effect = RuntimeError("unexpected crash")
        with patch("api.get_model", return_value=mock_model):
            r = client.post(
                "/ocr",
                files={"file": ("doc.jpg", img, "image/jpeg")},
            )
        assert r.status_code == 500
