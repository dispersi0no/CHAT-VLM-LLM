"""Tests for vllm_streamlit_adapter.py"""

from unittest.mock import MagicMock, patch

import pytest
import requests as req_lib
from PIL import Image

from vllm_streamlit_adapter import VLLMStreamlitAdapter

# ---------------------------------------------------------------------------
# Constants shared across tests
# ---------------------------------------------------------------------------

_MODEL = "rednote-hilab/dots.ocr"
_ENDPOINT = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_manager():
    """Pre-configured mock SingleContainerManager."""
    manager = MagicMock()
    manager.get_active_model.return_value = None
    manager.models_config = {}
    return manager


@pytest.fixture
def adapter(mock_manager):
    """VLLMStreamlitAdapter with all heavy dependencies mocked."""
    with patch("vllm_streamlit_adapter.SingleContainerManager") as MockSCM:
        MockSCM.return_value = mock_manager
        inst = VLLMStreamlitAdapter()
    return inst


@pytest.fixture
def ready_adapter(adapter):
    """Adapter pre-configured as if one model is healthy."""
    adapter.healthy_endpoints = {_MODEL: _ENDPOINT}
    adapter.model_limits = {_MODEL: 4096}
    adapter.available_models = [_MODEL]
    return adapter


@pytest.fixture
def sample_image():
    return Image.new("RGB", (100, 100), color="white")


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------


class TestInit:
    def test_sets_default_base_url(self, adapter):
        assert adapter.base_url == "http://localhost:8000"

    def test_sets_custom_base_url(self, mock_manager):
        with patch("vllm_streamlit_adapter.SingleContainerManager") as MockSCM:
            MockSCM.return_value = mock_manager
            a = VLLMStreamlitAdapter(base_url="http://myserver:9000")
        assert a.base_url == "http://myserver:9000"

    def test_model_endpoints_contains_expected_models(self, adapter):
        assert "rednote-hilab/dots.ocr" in adapter.model_endpoints
        assert "Qwen/Qwen2-VL-2B-Instruct" in adapter.model_endpoints
        assert "Qwen/Qwen3-VL-2B-Instruct" in adapter.model_endpoints

    def test_model_priorities_contains_expected_models(self, adapter):
        assert "rednote-hilab/dots.ocr" in adapter.model_priorities
        assert adapter.model_priorities["rednote-hilab/dots.ocr"] == 1

    def test_creates_single_container_manager(self, mock_manager):
        with patch("vllm_streamlit_adapter.SingleContainerManager") as MockSCM:
            MockSCM.return_value = mock_manager
            VLLMStreamlitAdapter()
        MockSCM.assert_called_once()

    def test_calls_check_all_connections_on_init(self, mock_manager):
        with patch("vllm_streamlit_adapter.SingleContainerManager") as MockSCM:
            MockSCM.return_value = mock_manager
            with patch.object(
                VLLMStreamlitAdapter, "check_all_connections", return_value=False
            ) as mock_check:
                VLLMStreamlitAdapter()
        mock_check.assert_called_once()


# ---------------------------------------------------------------------------
# TestCheckAllConnections
# ---------------------------------------------------------------------------


class TestCheckAllConnections:
    def test_no_active_model_returns_false(self, adapter, mock_manager):
        mock_manager.get_active_model.return_value = None
        result = adapter.check_all_connections()
        assert result is False

    def test_no_active_model_clears_available_models(self, adapter, mock_manager):
        adapter.available_models = [_MODEL]
        mock_manager.get_active_model.return_value = None
        adapter.check_all_connections()
        assert adapter.available_models == []

    def test_active_config_missing_returns_false(self, adapter, mock_manager):
        mock_manager.get_active_model.return_value = "dots_ocr"
        mock_manager.models_config = {}
        result = adapter.check_all_connections()
        assert result is False

    @patch("vllm_streamlit_adapter.requests.get")
    def test_health_200_and_matching_model_returns_true(
        self, mock_get, adapter, mock_manager
    ):
        mock_manager.get_active_model.return_value = "dots_ocr"
        mock_manager.models_config = {
            "dots_ocr": {
                "model_path": _MODEL,
                "port": 8000,
                "display_name": "dots.ocr",
            }
        }
        mock_health = MagicMock(status_code=200)
        mock_models = MagicMock(status_code=200)
        mock_models.json.return_value = {
            "data": [{"id": _MODEL, "max_model_len": 4096}]
        }
        mock_get.side_effect = [mock_health, mock_models]

        result = adapter.check_all_connections()

        assert result is True
        assert _MODEL in adapter.available_models
        assert _MODEL in adapter.healthy_endpoints
        assert adapter.model_limits[_MODEL] == 4096

    @patch("vllm_streamlit_adapter.requests.get")
    def test_health_check_non_200_returns_false(self, mock_get, adapter, mock_manager):
        mock_manager.get_active_model.return_value = "dots_ocr"
        mock_manager.models_config = {
            "dots_ocr": {
                "model_path": _MODEL,
                "port": 8000,
                "display_name": "dots.ocr",
            }
        }
        mock_get.return_value = MagicMock(status_code=503)

        result = adapter.check_all_connections()

        assert result is False

    @patch("vllm_streamlit_adapter.requests.get")
    def test_model_not_found_in_api_response_returns_false(
        self, mock_get, adapter, mock_manager
    ):
        mock_manager.get_active_model.return_value = "dots_ocr"
        mock_manager.models_config = {
            "dots_ocr": {
                "model_path": _MODEL,
                "port": 8000,
                "display_name": "dots.ocr",
            }
        }
        mock_health = MagicMock(status_code=200)
        mock_models = MagicMock(status_code=200)
        mock_models.json.return_value = {"data": [{"id": "other/model"}]}
        mock_get.side_effect = [mock_health, mock_models]

        result = adapter.check_all_connections()

        assert result is False
        assert _MODEL not in adapter.available_models

    @patch("vllm_streamlit_adapter.requests.get")
    def test_connection_exception_returns_false(self, mock_get, adapter, mock_manager):
        mock_manager.get_active_model.return_value = "dots_ocr"
        mock_manager.models_config = {
            "dots_ocr": {
                "model_path": _MODEL,
                "port": 8000,
                "display_name": "dots.ocr",
            }
        }
        mock_get.side_effect = req_lib.exceptions.ConnectionError("refused")

        result = adapter.check_all_connections()

        assert result is False


# ---------------------------------------------------------------------------
# TestGetEndpointForModel
# ---------------------------------------------------------------------------


class TestGetEndpointForModel:
    def test_known_model_returns_correct_endpoint(self, ready_adapter):
        result = ready_adapter.get_endpoint_for_model(_MODEL)
        assert result == _ENDPOINT

    def test_unknown_model_returns_base_url_fallback(self, adapter):
        adapter.healthy_endpoints = {}
        result = adapter.get_endpoint_for_model("unknown/model")
        assert result == adapter.base_url


# ---------------------------------------------------------------------------
# TestEnsureModelAvailable
# ---------------------------------------------------------------------------


class TestEnsureModelAvailable:
    def test_model_already_in_healthy_endpoints_returns_true(self, ready_adapter):
        result = ready_adapter.ensure_model_available(_MODEL)
        assert result is True

    def test_model_not_in_config_returns_false(self, adapter, mock_manager):
        adapter.healthy_endpoints = {}
        mock_manager.models_config = {}
        result = adapter.ensure_model_available(_MODEL)
        assert result is False

    def test_model_found_in_config_calls_start_single_container(
        self, adapter, mock_manager
    ):
        adapter.healthy_endpoints = {}
        mock_manager.models_config = {
            "dots_ocr": {
                "model_path": _MODEL,
                "port": 8000,
                "display_name": "dots.ocr",
            }
        }
        mock_manager.start_single_container.return_value = (True, "Started")

        with patch.object(adapter, "check_all_connections"):
            with patch("vllm_streamlit_adapter.time.sleep"):
                adapter.ensure_model_available(_MODEL)

        mock_manager.start_single_container.assert_called_once_with("dots_ocr")

    def test_successful_start_refreshes_connections(self, adapter, mock_manager):
        adapter.healthy_endpoints = {}
        mock_manager.models_config = {
            "dots_ocr": {
                "model_path": _MODEL,
                "port": 8000,
                "display_name": "dots.ocr",
            }
        }
        mock_manager.start_single_container.return_value = (True, "Started")

        with patch.object(adapter, "check_all_connections") as mock_check:
            with patch("vllm_streamlit_adapter.time.sleep"):
                adapter.ensure_model_available(_MODEL)

        mock_check.assert_called_once()

    def test_container_start_success_returns_true_when_model_becomes_available(
        self, adapter, mock_manager
    ):
        adapter.healthy_endpoints = {}
        mock_manager.models_config = {
            "dots_ocr": {
                "model_path": _MODEL,
                "port": 8000,
                "display_name": "dots.ocr",
            }
        }
        mock_manager.start_single_container.return_value = (True, "Started")

        def _add_model(*args, **kwargs):
            adapter.healthy_endpoints[_MODEL] = _ENDPOINT

        with patch.object(adapter, "check_all_connections", side_effect=_add_model):
            with patch("vllm_streamlit_adapter.time.sleep"):
                result = adapter.ensure_model_available(_MODEL)

        assert result is True

    def test_container_start_fails_returns_false(self, adapter, mock_manager):
        adapter.healthy_endpoints = {}
        mock_manager.models_config = {
            "dots_ocr": {
                "model_path": _MODEL,
                "port": 8000,
                "display_name": "dots.ocr",
            }
        }
        mock_manager.start_single_container.return_value = (False, "Failed to start")

        result = adapter.ensure_model_available(_MODEL)

        assert result is False


# ---------------------------------------------------------------------------
# TestGetRecommendedModels
# ---------------------------------------------------------------------------


class TestGetRecommendedModels:
    def test_sorts_available_models_by_priority(self, adapter):
        adapter.available_models = [
            "Qwen/Qwen2-VL-7B-Instruct",  # priority 5
            "rednote-hilab/dots.ocr",  # priority 1
            "Qwen/Qwen2-VL-2B-Instruct",  # priority 3
        ]
        result = adapter.get_recommended_models()
        assert result[0] == "rednote-hilab/dots.ocr"
        assert result[-1] == "Qwen/Qwen2-VL-7B-Instruct"

    def test_unknown_model_gets_priority_999_placed_last(self, adapter):
        adapter.available_models = [
            "unknown/model",  # priority 999
            "rednote-hilab/dots.ocr",  # priority 1
        ]
        result = adapter.get_recommended_models()
        assert result[0] == "rednote-hilab/dots.ocr"
        assert result[-1] == "unknown/model"

    def test_empty_available_models_returns_empty_list(self, adapter):
        adapter.available_models = []
        result = adapter.get_recommended_models()
        assert result == []


# ---------------------------------------------------------------------------
# TestGetAvailableModels
# ---------------------------------------------------------------------------


class TestGetAvailableModels:
    @patch("vllm_streamlit_adapter.requests.get")
    def test_successful_response_populates_available_models(self, mock_get, adapter):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {
            "data": [{"id": _MODEL, "max_model_len": 4096}]
        }
        mock_get.return_value = mock_response

        result = adapter.get_available_models()

        assert _MODEL in result
        assert adapter.model_limits[_MODEL] == 4096

    @patch("vllm_streamlit_adapter.requests.get")
    def test_successful_response_uses_default_token_limit_when_absent(
        self, mock_get, adapter
    ):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {
            "data": [{"id": _MODEL}]  # no max_model_len key
        }
        mock_get.return_value = mock_response

        adapter.get_available_models()

        assert adapter.model_limits[_MODEL] == 1024

    @patch("vllm_streamlit_adapter.requests.get")
    def test_api_error_returns_empty_list(self, mock_get, adapter):
        mock_get.return_value = MagicMock(status_code=500)
        result = adapter.get_available_models()
        assert result == []

    @patch("vllm_streamlit_adapter.requests.get")
    def test_connection_exception_returns_empty_list(self, mock_get, adapter):
        mock_get.side_effect = req_lib.exceptions.ConnectionError("refused")
        result = adapter.get_available_models()
        assert result == []


# ---------------------------------------------------------------------------
# TestGetModelMaxTokens
# ---------------------------------------------------------------------------


class TestGetModelMaxTokens:
    def test_known_model_returns_correct_limit(self, ready_adapter):
        result = ready_adapter.get_model_max_tokens(_MODEL)
        assert result == 4096

    def test_unknown_model_returns_default_1024(self, adapter):
        adapter.model_limits = {}
        result = adapter.get_model_max_tokens("unknown/model")
        assert result == 1024

    def test_missing_model_limits_attr_returns_default_1024(self, adapter):
        if hasattr(adapter, "model_limits"):
            del adapter.model_limits
        result = adapter.get_model_max_tokens(_MODEL)
        assert result == 1024


# ---------------------------------------------------------------------------
# TestProcessImage
# ---------------------------------------------------------------------------


class TestProcessImage:
    def test_model_unavailable_returns_failure_dict(self, adapter, sample_image):
        with patch.object(adapter, "ensure_model_available", return_value=False):
            result = adapter.process_image(sample_image, "Extract text", _MODEL)

        assert result["success"] is False
        assert "error" in result
        assert result["text"] == ""

    @patch("vllm_streamlit_adapter.requests.post")
    def test_successful_post_200_returns_success(
        self, mock_post, ready_adapter, sample_image
    ):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "extracted text"}}],
            "usage": {"total_tokens": 100},
        }
        mock_post.return_value = mock_response

        with patch.object(ready_adapter, "ensure_model_available", return_value=True):
            result = ready_adapter.process_image(sample_image, "Extract text", _MODEL)

        assert result["success"] is True
        assert result["text"] == "extracted text"
        assert "processing_time" in result

    @patch("vllm_streamlit_adapter.requests.post")
    def test_max_tokens_exceeds_model_limit_adjusts_down(
        self, mock_post, ready_adapter, sample_image
    ):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "text"}}],
            "usage": {"total_tokens": 50},
        }
        mock_post.return_value = mock_response

        with patch.object(ready_adapter, "ensure_model_available", return_value=True):
            result = ready_adapter.process_image(
                sample_image, "Extract text", _MODEL, max_tokens=9999
            )

        assert result["success"] is True
        assert result["actual_max_tokens"] <= 4096

    @patch("vllm_streamlit_adapter.requests.post")
    def test_input_token_estimation_triggers_further_adjustment(
        self, mock_post, ready_adapter, sample_image
    ):
        # When max_tokens equals the model limit (4096), the estimated input-token
        # overhead (prompt words + image placeholder) pushes the combined total above
        # the model limit.  The adapter must automatically reduce max_tokens so that
        # input + output tokens stay within the model's capacity.
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "text"}}],
            "usage": {"total_tokens": 10},
        }
        mock_post.return_value = mock_response

        with patch.object(ready_adapter, "ensure_model_available", return_value=True):
            result = ready_adapter.process_image(
                sample_image, "Extract text", _MODEL, max_tokens=4096
            )

        assert result["success"] is True
        # actual_max_tokens must be reduced below the model limit to reserve space
        # for the estimated input tokens
        assert result["actual_max_tokens"] < 4096

    @patch("vllm_streamlit_adapter.requests.post")
    def test_post_non_200_generic_returns_failure(
        self, mock_post, ready_adapter, sample_image
    ):
        mock_response = MagicMock(status_code=400)
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response

        with patch.object(ready_adapter, "ensure_model_available", return_value=True):
            result = ready_adapter.process_image(sample_image, "Extract text", _MODEL)

        assert result["success"] is False
        assert "error" in result

    @patch("vllm_streamlit_adapter.requests.post")
    def test_post_non_200_with_token_error_in_response_returns_failure(
        self, mock_post, ready_adapter, sample_image
    ):
        mock_response = MagicMock(status_code=400)
        mock_response.text = "max_tokens value exceeds model limit"
        mock_post.return_value = mock_response

        with patch.object(ready_adapter, "ensure_model_available", return_value=True):
            result = ready_adapter.process_image(sample_image, "Extract text", _MODEL)

        assert result["success"] is False

    @patch("vllm_streamlit_adapter.requests.post")
    def test_request_exception_returns_failure(
        self, mock_post, ready_adapter, sample_image
    ):
        mock_post.side_effect = req_lib.exceptions.ConnectionError("refused")

        with patch.object(ready_adapter, "ensure_model_available", return_value=True):
            result = ready_adapter.process_image(sample_image, "Extract text", _MODEL)

        assert result["success"] is False
        assert result["text"] == ""
        assert result["processing_time"] == 0

    @patch("vllm_streamlit_adapter.requests.post")
    def test_rgba_image_converted_to_rgb_before_sending(self, mock_post, ready_adapter):
        rgba_image = Image.new("RGBA", (50, 50), color=(255, 0, 0, 128))
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "text"}}],
            "usage": {"total_tokens": 10},
        }
        mock_post.return_value = mock_response

        with patch.object(ready_adapter, "ensure_model_available", return_value=True):
            result = ready_adapter.process_image(rgba_image, "Describe", _MODEL)

        assert result["success"] is True
        mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# TestChatWithImage
# ---------------------------------------------------------------------------


class TestChatWithImage:
    def test_delegates_to_process_image_with_correct_args(self, adapter, sample_image):
        expected = {"success": True, "text": "ok"}
        with patch.object(adapter, "process_image", return_value=expected) as mock_pi:
            result = adapter.chat_with_image(sample_image, "Describe", _MODEL)

        mock_pi.assert_called_once_with(sample_image, "Describe", _MODEL)
        assert result == expected


# ---------------------------------------------------------------------------
# TestGetServerStatus
# ---------------------------------------------------------------------------


class TestGetServerStatus:
    def test_no_healthy_endpoints_returns_error_status(self, adapter):
        adapter.healthy_endpoints = {}
        adapter.available_models = []
        status = adapter.get_server_status()
        assert status["status"] == "error"

    def test_has_healthy_endpoints_returns_healthy_status(self, ready_adapter):
        status = ready_adapter.get_server_status()
        assert status["status"] == "healthy"

    def test_returns_required_keys(self, ready_adapter):
        status = ready_adapter.get_server_status()
        for key in (
            "status",
            "healthy_endpoints",
            "total_endpoints",
            "available_models",
            "model_limits",
            "endpoints",
        ):
            assert key in status

    def test_healthy_endpoints_count_is_correct(self, ready_adapter):
        status = ready_adapter.get_server_status()
        assert status["healthy_endpoints"] == 1

    def test_available_models_included_in_status(self, ready_adapter):
        status = ready_adapter.get_server_status()
        assert _MODEL in status["available_models"]

    def test_total_endpoints_reflects_model_endpoints_map(self, adapter):
        status = adapter.get_server_status()
        assert status["total_endpoints"] == len(adapter.model_endpoints)


# ---------------------------------------------------------------------------
# TestCheckConnection
# ---------------------------------------------------------------------------


class TestCheckConnection:
    def test_delegates_to_check_all_connections(self, adapter):
        with patch.object(
            adapter, "check_all_connections", return_value=True
        ) as mock_check:
            result = adapter.check_connection()
        mock_check.assert_called_once()
        assert result is True

    def test_propagates_false_from_check_all_connections(self, adapter):
        with patch.object(adapter, "check_all_connections", return_value=False):
            result = adapter.check_connection()
        assert result is False
