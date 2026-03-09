"""Tests for single_container_manager.py"""

from unittest.mock import MagicMock, mock_open, patch

import docker
import pytest
import requests as req_lib
import yaml

from single_container_manager import SingleContainerManager

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_config():
    return {
        "dots_ocr": {
            "model_path": "rednote-hilab/dots.ocr",
            "display_name": "dots.ocr",
            "port": 8100,
            "memory_gb": 4,
            "startup_time": 60,
            "container_name": "vllm-dots-ocr",
            "context_length": 4096,
            "description": "Test model",
            "compose_service": "vllm-dots-ocr",
        }
    }


@pytest.fixture
def manager(sample_config):
    """Create a SingleContainerManager with mocked Docker client and config."""
    with patch.object(
        SingleContainerManager, "_load_vllm_config", return_value=sample_config
    ):
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = MagicMock()
            mgr = SingleContainerManager()
    return mgr


# ---------------------------------------------------------------------------
# TestLoadVllmConfig
# ---------------------------------------------------------------------------


class TestLoadVllmConfig:
    def test_successful_load_returns_dict(self):
        yaml_content = "vllm:\n  dots_ocr:\n    model_path: rednote-hilab/dots.ocr\n"
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = SingleContainerManager._load_vllm_config()

        assert isinstance(result, dict)
        assert "dots_ocr" in result
        assert result["dots_ocr"]["model_path"] == "rednote-hilab/dots.ocr"

    def test_missing_config_file_raises_file_not_found_error(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError, match="config.yaml"):
                SingleContainerManager._load_vllm_config()

    def test_invalid_yaml_raises_value_error(self):
        with patch("builtins.open", mock_open(read_data="key: value")):
            with patch(
                "yaml.safe_load", side_effect=yaml.YAMLError("bad yaml content")
            ):
                with pytest.raises(ValueError, match="Failed to parse"):
                    SingleContainerManager._load_vllm_config()

    def test_missing_vllm_key_returns_empty_dict(self):
        yaml_content = "other_section:\n  foo: bar\n"
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = SingleContainerManager._load_vllm_config()

        assert result == {}


# ---------------------------------------------------------------------------
# TestGetContainerStatus
# ---------------------------------------------------------------------------


class TestGetContainerStatus:
    def test_running_container_returns_correct_status(self, manager):
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.attrs = {
            "State": {},
            "Created": "2024-01-01T00:00:00Z",
        }
        manager.client.containers.get.return_value = mock_container

        status = manager.get_container_status("vllm-dots-ocr")

        assert status["exists"] is True
        assert status["running"] is True
        assert status["status"] == "running"
        assert status["health"] == "unknown"

    def test_container_with_health_check_returns_health_status(self, manager):
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_container.attrs = {
            "State": {
                "Health": {"Status": "healthy"},
                "StartedAt": "2024-01-01T00:00:01Z",
            },
            "Created": "2024-01-01T00:00:00Z",
        }
        manager.client.containers.get.return_value = mock_container

        status = manager.get_container_status("vllm-dots-ocr")

        assert status["health"] == "healthy"
        assert status["exists"] is True

    def test_not_found_returns_not_found_dict(self, manager):
        manager.client.containers.get.side_effect = docker.errors.NotFound(
            "container not found"
        )

        status = manager.get_container_status("nonexistent")

        assert status["exists"] is False
        assert status["running"] is False
        assert status["status"] == "not_found"

    def test_general_exception_returns_error_dict(self, manager):
        manager.client.containers.get.side_effect = RuntimeError("connection failed")

        status = manager.get_container_status("vllm-dots-ocr")

        assert status["exists"] is False
        assert status["running"] is False
        assert status["status"] == "error"
        assert "connection failed" in status["error"]


# ---------------------------------------------------------------------------
# TestCheckApiHealth
# ---------------------------------------------------------------------------


class TestCheckApiHealth:
    @patch("single_container_manager.requests.get")
    def test_healthy_api_returns_true_and_message(self, mock_get, manager):
        mock_health = MagicMock(status_code=200)
        mock_models = MagicMock(status_code=200)
        mock_models.json.return_value = {"data": [{"id": "model"}]}
        mock_get.side_effect = [mock_health, mock_models]

        healthy, msg = manager.check_api_health(8100)

        assert healthy is True
        assert msg == "API healthy"

    @patch("single_container_manager.requests.get")
    def test_health_endpoint_non_200_returns_false(self, mock_get, manager):
        mock_health = MagicMock(status_code=503)
        mock_get.return_value = mock_health

        healthy, msg = manager.check_api_health(8100)

        assert healthy is False
        assert "503" in msg

    @patch("single_container_manager.requests.get")
    def test_models_endpoint_non_200_returns_false(self, mock_get, manager):
        mock_health = MagicMock(status_code=200)
        mock_models = MagicMock(status_code=500)
        mock_get.side_effect = [mock_health, mock_models]

        healthy, msg = manager.check_api_health(8100)

        assert healthy is False
        assert "500" in msg

    @patch("single_container_manager.requests.get")
    def test_empty_models_data_returns_false(self, mock_get, manager):
        mock_health = MagicMock(status_code=200)
        mock_models = MagicMock(status_code=200)
        mock_models.json.return_value = {"data": []}
        mock_get.side_effect = [mock_health, mock_models]

        healthy, msg = manager.check_api_health(8100)

        assert healthy is False
        assert "No models available" in msg

    @patch("single_container_manager.requests.get")
    def test_connection_error_returns_false(self, mock_get, manager):
        mock_get.side_effect = req_lib.exceptions.ConnectionError()

        healthy, msg = manager.check_api_health(8100)

        assert healthy is False
        assert msg == "Connection refused"

    @patch("single_container_manager.requests.get")
    def test_timeout_returns_false(self, mock_get, manager):
        mock_get.side_effect = req_lib.exceptions.Timeout()

        healthy, msg = manager.check_api_health(8100)

        assert healthy is False
        assert msg == "Request timeout"

    @patch("single_container_manager.requests.get")
    def test_general_exception_returns_false(self, mock_get, manager):
        mock_get.side_effect = RuntimeError("unexpected error")

        healthy, msg = manager.check_api_health(8100)

        assert healthy is False
        assert "unexpected error" in msg


# ---------------------------------------------------------------------------
# TestGetActiveModel
# ---------------------------------------------------------------------------


class TestGetActiveModel:
    def test_returns_model_key_when_container_running_and_api_healthy(self, manager):
        with patch.object(
            manager, "get_container_status", return_value={"running": True}
        ):
            with patch.object(
                manager, "check_api_health", return_value=(True, "API healthy")
            ):
                result = manager.get_active_model()

        assert result == "dots_ocr"

    def test_returns_none_when_no_containers_running(self, manager):
        with patch.object(
            manager, "get_container_status", return_value={"running": False}
        ):
            result = manager.get_active_model()

        assert result is None

    def test_returns_none_when_container_running_but_api_unhealthy(self, manager):
        with patch.object(
            manager, "get_container_status", return_value={"running": True}
        ):
            with patch.object(
                manager,
                "check_api_health",
                return_value=(False, "Connection refused"),
            ):
                result = manager.get_active_model()

        assert result is None

    def test_sets_current_active_model_when_healthy(self, manager):
        with patch.object(
            manager, "get_container_status", return_value={"running": True}
        ):
            with patch.object(
                manager, "check_api_health", return_value=(True, "API healthy")
            ):
                manager.get_active_model()

        assert manager.current_active_model == "dots_ocr"

    def test_clears_current_active_model_when_none_healthy(self, manager):
        manager.current_active_model = "dots_ocr"

        with patch.object(
            manager, "get_container_status", return_value={"running": False}
        ):
            manager.get_active_model()

        assert manager.current_active_model is None


# ---------------------------------------------------------------------------
# TestStopAllContainers
# ---------------------------------------------------------------------------


class TestStopAllContainers:
    def test_stops_running_containers(self, manager):
        mock_container = MagicMock()

        with patch.object(
            manager, "get_container_status", return_value={"running": True}
        ):
            manager.client.containers.get.return_value = mock_container
            stopped, failed = manager.stop_all_containers()

        assert "dots_ocr" in stopped
        assert failed == []
        mock_container.stop.assert_called_once_with(timeout=10)
        mock_container.remove.assert_called_once()

    def test_handles_not_found_after_status_check(self, manager):
        with patch.object(
            manager, "get_container_status", return_value={"running": True}
        ):
            manager.client.containers.get.side_effect = docker.errors.NotFound(
                "already gone"
            )
            stopped, failed = manager.stop_all_containers()

        assert "dots_ocr" in stopped
        assert failed == []

    def test_handles_general_exception_adds_to_failed(self, manager):
        with patch.object(
            manager, "get_container_status", return_value={"running": True}
        ):
            manager.client.containers.get.side_effect = RuntimeError("docker error")
            stopped, failed = manager.stop_all_containers()

        assert stopped == []
        assert len(failed) == 1
        assert "dots_ocr" in failed[0]

    def test_skips_non_running_containers(self, manager):
        with patch.object(
            manager, "get_container_status", return_value={"running": False}
        ):
            stopped, failed = manager.stop_all_containers()

        assert stopped == []
        assert failed == []
        manager.client.containers.get.assert_not_called()


# ---------------------------------------------------------------------------
# TestBuildDockerCommand
# ---------------------------------------------------------------------------


class TestBuildDockerCommand:
    def test_contains_model_path(self, manager, sample_config):
        cmd = manager._build_docker_command("dots_ocr", sample_config["dots_ocr"])

        assert "--model" in cmd
        assert "rednote-hilab/dots.ocr" in cmd

    def test_includes_port_mapping(self, manager, sample_config):
        cmd = manager._build_docker_command("dots_ocr", sample_config["dots_ocr"])

        assert "-p" in cmd
        assert "8100:8000" in cmd

    def test_includes_gpu_flags(self, manager, sample_config):
        cmd = manager._build_docker_command("dots_ocr", sample_config["dots_ocr"])

        assert "--gpus" in cmd
        assert "all" in cmd

    def test_includes_huggingface_cache_mount(self, manager, sample_config):
        with patch("os.path.expanduser", return_value="/home/user/.cache/huggingface"):
            cmd = manager._build_docker_command("dots_ocr", sample_config["dots_ocr"])

        assert "-v" in cmd
        assert any("/root/.cache/huggingface" in s for s in cmd)

    def test_respects_context_length_from_config(self, manager, sample_config):
        cmd = manager._build_docker_command("dots_ocr", sample_config["dots_ocr"])

        assert "--max-model-len" in cmd
        idx = cmd.index("--max-model-len")
        assert cmd[idx + 1] == "4096"

    def test_default_context_length_when_key_missing(self, manager, sample_config):
        config = dict(sample_config["dots_ocr"])
        del config["context_length"]

        cmd = manager._build_docker_command("dots_ocr", config)

        idx = cmd.index("--max-model-len")
        assert cmd[idx + 1] == "4096"

    def test_returns_list_starting_with_docker_run(self, manager, sample_config):
        cmd = manager._build_docker_command("dots_ocr", sample_config["dots_ocr"])

        assert isinstance(cmd, list)
        assert cmd[0] == "docker"
        assert cmd[1] == "run"


# ---------------------------------------------------------------------------
# TestGetSystemStatus
# ---------------------------------------------------------------------------


class TestGetSystemStatus:
    def test_returns_correct_top_level_structure(self, manager):
        with patch.object(manager, "get_active_model", return_value=None):
            with patch.object(
                manager, "get_container_status", return_value={"running": False}
            ):
                status = manager.get_system_status()

        assert "active_model" in status
        assert "active_model_name" in status
        assert "total_memory_usage" in status
        assert "models" in status
        assert "principle" in status

    def test_models_dict_contains_all_config_keys(self, manager):
        with patch.object(manager, "get_active_model", return_value=None):
            with patch.object(
                manager, "get_container_status", return_value={"running": False}
            ):
                status = manager.get_system_status()

        assert "dots_ocr" in status["models"]

    def test_active_model_name_is_none_when_no_active_model(self, manager):
        with patch.object(manager, "get_active_model", return_value=None):
            with patch.object(
                manager, "get_container_status", return_value={"running": False}
            ):
                status = manager.get_system_status()

        assert status["active_model"] is None
        assert status["active_model_name"] is None

    def test_sums_memory_only_for_healthy_models(self, manager, sample_config):
        with patch.object(manager, "get_active_model", return_value="dots_ocr"):
            with patch.object(
                manager, "get_container_status", return_value={"running": True}
            ):
                with patch.object(
                    manager, "check_api_health", return_value=(True, "API healthy")
                ):
                    status = manager.get_system_status()

        assert status["total_memory_usage"] == sample_config["dots_ocr"]["memory_gb"]

    def test_does_not_count_memory_for_unhealthy_models(self, manager):
        with patch.object(manager, "get_active_model", return_value=None):
            with patch.object(
                manager, "get_container_status", return_value={"running": True}
            ):
                with patch.object(
                    manager,
                    "check_api_health",
                    return_value=(False, "Connection refused"),
                ):
                    status = manager.get_system_status()

        assert status["total_memory_usage"] == 0


# ---------------------------------------------------------------------------
# TestStartSingleContainer
# ---------------------------------------------------------------------------


class TestStartSingleContainer:
    def test_model_not_in_config_returns_false_with_message(self, manager):
        success, msg = manager.start_single_container("nonexistent_model")

        assert success is False
        assert "nonexistent_model" in msg

    def test_already_active_model_with_healthy_api_returns_true(
        self, manager, sample_config
    ):
        with patch.object(manager, "get_active_model", return_value="dots_ocr"):
            with patch.object(
                manager, "check_api_health", return_value=(True, "API healthy")
            ):
                success, msg = manager.start_single_container("dots_ocr")

        assert success is True
        assert sample_config["dots_ocr"]["display_name"] in msg

    @patch("single_container_manager.subprocess.run")
    @patch("single_container_manager.time.sleep")
    @patch("single_container_manager.time.time", return_value=0)
    def test_successful_start_returns_true(
        self, mock_time, mock_sleep, mock_subprocess, manager, sample_config
    ):
        mock_subprocess.return_value = MagicMock(returncode=0)

        with patch.object(manager, "get_active_model", return_value=None):
            with patch.object(manager, "stop_all_containers", return_value=([], [])):
                with patch.object(
                    manager,
                    "get_container_status",
                    return_value={"running": True, "status": "running"},
                ):
                    with patch.object(
                        manager,
                        "check_api_health",
                        return_value=(True, "API healthy"),
                    ):
                        success, msg = manager.start_single_container("dots_ocr")

        assert success is True
        assert sample_config["dots_ocr"]["display_name"] in msg
        mock_subprocess.assert_called_once()

    @patch("single_container_manager.subprocess.run")
    @patch("single_container_manager.time.sleep")
    def test_subprocess_failure_returns_false(
        self, mock_sleep, mock_subprocess, manager
    ):
        mock_subprocess.return_value = MagicMock(returncode=1, stderr="start error")

        with patch.object(manager, "get_active_model", return_value=None):
            with patch.object(manager, "stop_all_containers", return_value=([], [])):
                success, msg = manager.start_single_container("dots_ocr")

        assert success is False
        assert "start error" in msg

    @patch("single_container_manager.subprocess.run")
    @patch("single_container_manager.time.sleep")
    @patch("single_container_manager.time.time")
    def test_startup_timeout_returns_false(
        self, mock_time, mock_sleep, mock_subprocess, manager, sample_config
    ):
        mock_subprocess.return_value = MagicMock(returncode=0)
        # First call sets start_time=0; second call in while-condition returns value
        # exceeding max_wait so the loop body never executes.
        mock_time.side_effect = [0, 200]

        with patch.object(manager, "get_active_model", return_value=None):
            with patch.object(manager, "stop_all_containers", return_value=([], [])):
                success, msg = manager.start_single_container("dots_ocr")

        assert success is False
        assert str(sample_config["dots_ocr"]["startup_time"]) in msg

    @patch("single_container_manager.subprocess.run")
    @patch("single_container_manager.time.sleep")
    def test_subprocess_exception_returns_false(
        self, mock_sleep, mock_subprocess, manager
    ):
        mock_subprocess.side_effect = OSError("docker not found")

        with patch.object(manager, "get_active_model", return_value=None):
            with patch.object(manager, "stop_all_containers", return_value=([], [])):
                success, msg = manager.start_single_container("dots_ocr")

        assert success is False
        assert "docker not found" in msg
