"""Shared pytest fixtures."""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

# Ensure project root is in sys.path for imports
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---------------------------------------------------------------------------
# Stub heavy optional dependencies so test modules can be collected even when
# the real packages are not installed (no GPU / no ML environment).
# ---------------------------------------------------------------------------


def _make_torch_mock() -> MagicMock:
    """Build a MagicMock that looks enough like torch for our code."""
    torch_mock = MagicMock(name="torch")

    # cuda sub-module
    cuda_mock = MagicMock(name="torch.cuda")
    cuda_mock.is_available.return_value = False
    cuda_mock.empty_cache.return_value = None
    cuda_mock.synchronize.return_value = None
    cuda_mock.device_count.return_value = 0
    cuda_mock.memory_allocated.return_value = 0
    cuda_mock.memory_reserved.return_value = 0
    torch_mock.cuda = cuda_mock

    # backends.mps sub-module
    backends_mock = MagicMock(name="torch.backends")
    mps_mock = MagicMock(name="torch.backends.mps")
    mps_mock.is_available.return_value = False
    backends_mock.mps = mps_mock
    torch_mock.backends = backends_mock

    # dtype sentinels
    torch_mock.float16 = "float16"
    torch_mock.bfloat16 = "bfloat16"
    torch_mock.float32 = "float32"

    return torch_mock


def _stub(name: str) -> MagicMock:
    """Return (and register) a simple MagicMock for *name* if not yet present."""
    if name not in sys.modules:
        mock = MagicMock(name=name)
        sys.modules[name] = mock
        return mock
    return sys.modules[name]  # type: ignore[return-value]


# Torch (and sub-packages used at import time)
if "torch" not in sys.modules:
    _torch = _make_torch_mock()
    sys.modules["torch"] = _torch
    sys.modules["torch.cuda"] = _torch.cuda
    sys.modules["torch.backends"] = _torch.backends
    sys.modules["torch.backends.mps"] = _torch.backends.mps

# Transformers
for _pkg in (
    "transformers",
    "transformers.utils",
    "transformers.models",
):
    _stub(_pkg)

# Pandas (required by utils/table_parser.py and utils/table_renderer.py)
_stub("pandas")

# OpenCV (required by utils/image_processor.py)
_stub("cv2")

# Streamlit (optional, required by utils/table_renderer.py)
_stub("streamlit")

# qwen_vl_utils (optional dependency of models/qwen_vl.py)
_stub("qwen_vl_utils")

# Docker SDK (required by single_container_manager.py; not installed in CI)
if "docker" not in sys.modules:
    _docker_mock = MagicMock(name="docker")

    class _NotFound(Exception):
        pass

    class _APIError(Exception):
        pass

    _docker_errors = MagicMock(name="docker.errors")
    _docker_errors.NotFound = _NotFound
    _docker_errors.APIError = _APIError
    _docker_mock.errors = _docker_errors
    sys.modules["docker"] = _docker_mock
    sys.modules["docker.errors"] = _docker_errors
