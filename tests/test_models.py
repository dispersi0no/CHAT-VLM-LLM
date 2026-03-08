"""Tests for model integration."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from models import ModelLoader
from models.base_model import BaseModel
from models.dots_ocr import DotsOCRFinalModel, DotsOCRModel

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img_array = np.ones((100, 200, 3), dtype=np.uint8) * 255
    return Image.fromarray(img_array)


@pytest.fixture
def config_path():
    """Get path to test config."""
    return "config.yaml"


@pytest.fixture
def mock_model(sample_image):
    """A concrete BaseModel subclass for testing without GPU."""

    class _MockModel(BaseModel):
        def load_model(self):
            pass

        def process_image(self, image, prompt=None):
            return "mock_result"

    return _MockModel({"model_path": "test/path", "precision": "fp16", "name": "mock"})


# ---------------------------------------------------------------------------
# DotsOCR alias
# ---------------------------------------------------------------------------


class TestDotsOCRAlias:
    """Verify the backward-compat alias introduced after the refactor."""

    def test_alias_is_same_class(self):
        assert DotsOCRFinalModel is DotsOCRModel

    def test_dots_ocr_in_registry(self):
        assert "dots_ocr" in ModelLoader.MODEL_REGISTRY
        assert "dots_ocr_final" in ModelLoader.MODEL_REGISTRY
        assert ModelLoader.MODEL_REGISTRY["dots_ocr"] is DotsOCRModel
        assert ModelLoader.MODEL_REGISTRY["dots_ocr_final"] is DotsOCRModel

    def test_dots_ocr_final_model_alias_instantiable(self):
        """DotsOCRFinalModel can be instantiated and behaves like DotsOCRModel."""
        cfg = {"model_path": "test/path", "precision": "fp16", "name": "test"}
        instance = DotsOCRFinalModel(cfg)
        assert isinstance(instance, DotsOCRModel)
        assert instance.precision == "fp16"
        info = instance.get_model_info()
        assert "model_id" in info
        assert info["loaded"] is False


# ---------------------------------------------------------------------------
# ModelLoader
# ---------------------------------------------------------------------------


class TestModelLoader:
    """Tests for ModelLoader class."""

    def test_load_config(self, config_path):
        """Test configuration loading."""
        config = ModelLoader.load_config()
        assert "transformers" in config
        assert "ocr" in config

    def test_get_available_models(self, config_path):
        """Test listing available models."""
        models = ModelLoader.MODEL_REGISTRY
        assert isinstance(models, dict)
        assert len(models) > 0
        assert "qwen3_vl_2b" in models or "dots_ocr" in models

    def test_registry_contains_expected_keys(self):
        """MODEL_REGISTRY must contain all expected model keys."""
        registry = ModelLoader.MODEL_REGISTRY
        for key in (
            "got_ocr",
            "qwen_vl_2b",
            "qwen3_vl_2b",
            "dots_ocr",
            "dots_ocr_final",
        ):
            assert key in registry, f"Expected '{key}' in MODEL_REGISTRY"

    def test_get_available_models_returns_list(self):
        """get_available_models() returns a list of dicts with at least 'id'."""
        available = ModelLoader.get_available_models()
        assert isinstance(available, list)
        for entry in available:
            assert "id" in entry
            assert entry["id"] in ModelLoader.MODEL_REGISTRY

    def test_get_available_models_contains_all_registry_keys(self):
        """Every key in MODEL_REGISTRY appears in get_available_models()."""
        available_ids = {m["id"] for m in ModelLoader.get_available_models()}
        for key in ModelLoader.MODEL_REGISTRY:
            assert key in available_ids

    def test_model_configuration(self, config_path):
        """Test model configuration structure."""
        config = ModelLoader.load_config()
        models_section = ModelLoader._get_models_section(config)
        for model_key, model_config in models_section.items():
            assert "name" in model_config
            assert "model_path" in model_config
            assert "precision" in model_config

    def test_get_model_config_valid_keys(self):
        """Each model key in registry resolves to a valid config dict."""
        config = ModelLoader.load_config()
        models_section = ModelLoader._get_models_section(config)
        for key in ("got_ocr", "qwen_vl_2b", "qwen3_vl_2b", "dots_ocr"):
            if key in models_section:
                cfg = models_section[key]
                assert isinstance(cfg, dict)
                assert "model_path" in cfg

    @pytest.mark.skip(reason="Requires model download and GPU")
    def test_load_model(self, config_path):
        """Test model loading (requires GPU and downloads)."""
        model = ModelLoader.load_model("got_ocr")
        assert model is not None
        assert isinstance(model, BaseModel)
        ModelLoader.unload_model("got_ocr")

    def test_model_caching(self):
        """Test that get_loaded_models returns a list."""
        loaded = ModelLoader.get_loaded_models()
        assert isinstance(loaded, list)

    def test_is_model_loaded_false_for_unloaded(self):
        """is_model_loaded returns False for a model that hasn't been loaded."""
        ModelLoader._loaded_models.clear()
        assert ModelLoader.is_model_loaded("got_ocr") is False

    def test_load_invalid_model_raises(self):
        """load_model raises ValueError for unknown model key."""
        with pytest.raises(ValueError, match="not found"):
            ModelLoader.load_model("nonexistent_model_xyz")

    def test_unload_not_loaded_returns_false(self):
        """unload_model returns False when model is not loaded."""
        ModelLoader._loaded_models.clear()
        result = ModelLoader.unload_model("got_ocr")
        assert result is False

    def test_get_available_vram_no_gpu(self):
        """get_available_vram returns 0.0 when no GPU is present."""
        vram = ModelLoader.get_available_vram()
        assert isinstance(vram, float)
        assert vram == 0.0


# ---------------------------------------------------------------------------
# BaseModel
# ---------------------------------------------------------------------------


class TestBaseModel:
    """Tests for BaseModel class."""

    def test_device_is_cpu_without_gpu(self, mock_model):
        """Without a real GPU the device should be 'cpu'."""
        assert mock_model.device == "cpu"

    def test_device_detection(self, mock_model):
        """Device is always a recognised string."""
        assert mock_model.device in ("cuda", "mps", "cpu")

    def test_get_device_cuda_path(self):
        """_get_device returns 'cuda' when torch.cuda.is_available() is True."""
        import torch

        with patch.object(torch.cuda, "is_available", return_value=True):
            with patch.object(
                torch.cuda,
                "get_device_properties",
                return_value=MagicMock(total_memory=8 * 1024**3),
            ):
                with patch.object(
                    torch.cuda, "get_device_name", return_value="Tesla T4"
                ):

                    class _M(BaseModel):
                        def load_model(self):
                            pass

                        def process_image(self, image, prompt=None):
                            return ""

                    m = _M({"model_path": "x"})
                    assert m.device == "cuda"

    def test_get_device_mps_path(self):
        """_get_device returns 'mps' when MPS is available."""
        import torch

        with patch.object(torch.cuda, "is_available", return_value=False):
            with patch.object(torch.backends.mps, "is_available", return_value=True):

                class _M(BaseModel):
                    def load_model(self):
                        pass

                    def process_image(self, image, prompt=None):
                        return ""

                m = _M({"model_path": "x"})
                assert m.device == "mps"

    def test_get_load_kwargs_cpu_path(self, mock_model):
        """_get_load_kwargs returns float32 dtype on CPU."""
        import torch

        kwargs = mock_model._get_load_kwargs()
        assert "trust_remote_code" in kwargs
        assert kwargs.get("torch_dtype") == torch.float32

    def test_get_load_kwargs_fp16_cuda(self):
        """_get_load_kwargs includes fp16 dtype when CUDA is available."""
        import torch

        with patch.object(torch.cuda, "is_available", return_value=True):

            class _M(BaseModel):
                def load_model(self):
                    pass

                def process_image(self, image, prompt=None):
                    return ""

            m = _M({"model_path": "x", "precision": "fp16"})
            kwargs = m._get_load_kwargs()
            assert kwargs.get("device_map") == "auto"
            assert kwargs.get("torch_dtype") == torch.float16

    def test_get_load_kwargs_bf16_cuda(self):
        """_get_load_kwargs includes bfloat16 dtype for bf16 precision."""
        import torch

        with patch.object(torch.cuda, "is_available", return_value=True):

            class _M(BaseModel):
                def load_model(self):
                    pass

                def process_image(self, image, prompt=None):
                    return ""

            m = _M({"model_path": "x", "precision": "bf16"})
            kwargs = m._get_load_kwargs()
            assert kwargs.get("torch_dtype") == torch.bfloat16

    def test_get_load_kwargs_int8_cuda(self):
        """_get_load_kwargs sets load_in_8bit for int8 precision."""
        import torch

        with patch.object(torch.cuda, "is_available", return_value=True):

            class _M(BaseModel):
                def load_model(self):
                    pass

                def process_image(self, image, prompt=None):
                    return ""

            m = _M({"model_path": "x", "precision": "int8"})
            kwargs = m._get_load_kwargs()
            assert kwargs.get("load_in_8bit") is True

    def test_extract_fields_colon_pattern(self, mock_model):
        """extract_fields parses 'Field: value' correctly."""
        text = "Name: John Doe\nAge: 30\nCity: New York"
        result = mock_model.extract_fields(text, ["Name", "Age", "City"])
        assert result["Name"] == "John Doe"
        assert result["Age"] == "30"
        assert result["City"] == "New York"

    def test_extract_fields_next_line_pattern(self, mock_model):
        """extract_fields reads the next line when no colon is present."""
        text = "Name\nJohn Doe\nOther"
        result = mock_model.extract_fields(text, ["Name"])
        assert result["Name"] == "John Doe"

    def test_extract_fields_missing_field(self, mock_model):
        """extract_fields returns empty string for missing field."""
        result = mock_model.extract_fields("hello world", ["NoSuchField"])
        assert result["NoSuchField"] == ""

    def test_extract_single_field_colon(self, mock_model):
        """_extract_single_field handles 'field: value' format."""
        val = mock_model._extract_single_field("Total: $42.00", "Total")
        assert val == "$42.00"

    def test_extract_single_field_not_found(self, mock_model):
        """_extract_single_field returns empty string when field absent."""
        val = mock_model._extract_single_field("no relevant content", "Date")
        assert val == ""

    def test_get_model_info_structure(self, mock_model):
        """get_model_info returns a dict with required keys."""
        info = mock_model.get_model_info()
        assert "model_id" in info
        assert "device" in info
        assert "config" in info
        assert "loaded" in info
        assert info["loaded"] is False

    def test_run_dispatches_to_process_image(self, mock_model, sample_image):
        """run() without kwargs calls process_image."""
        result = mock_model.run(sample_image, prompt="describe")
        assert result == "mock_result"

    def test_run_dispatches_to_chat_with_kwargs(self, mock_model, sample_image):
        """run() with prompt + kwargs delegates to chat()."""
        with patch.object(mock_model, "chat", return_value="chat_result") as mock_chat:
            result = mock_model.run(sample_image, prompt="describe", temperature=0.7)
            mock_chat.assert_called_once()
            assert result == "chat_result"

    def test_chat_default_uses_process_image(self, mock_model, sample_image):
        """Default chat() falls back to process_image."""
        result = mock_model.chat(sample_image, "hello")
        assert result == "mock_result"

    def test_unload_when_model_is_none(self, mock_model):
        """unload() is a no-op when model is not loaded."""
        mock_model.model = None
        mock_model.unload()
        assert mock_model.model is None

    def test_unload_clears_model(self, mock_model):
        """unload() sets model and processor to None."""
        mock_model.model = MagicMock()
        mock_model.processor = MagicMock()
        mock_model.unload()
        assert mock_model.model is None
        assert mock_model.processor is None

    def test_extract_fields_basic(self):
        """Test basic field extraction (legacy test preserved)."""

        class MockModel(BaseModel):
            def load_model(self):
                pass

            def process_image(self, image, prompt=None):
                return "test"

        model = MockModel({"model_path": "test", "precision": "fp16"})
        text = "Name: John Doe\nAge: 30"
        fields = model.extract_fields(text, ["Name", "Age"])

        assert isinstance(fields, dict)
        assert "Name" in fields
        assert "Age" in fields


# ---------------------------------------------------------------------------
# Integration tests (GPU required — always skipped in CI)
# ---------------------------------------------------------------------------


class TestModelIntegration:
    """Integration tests for models (require GPU and downloads)."""

    @pytest.mark.skip(reason="Requires model download and GPU")
    def test_got_ocr_inference(self, sample_image):
        """Test GOT-OCR model inference."""
        model = ModelLoader.load_model("got_ocr")
        result = model.process_image(sample_image)
        assert isinstance(result, str)
        ModelLoader.unload_model("got_ocr")

    @pytest.mark.skip(reason="Requires model download and GPU")
    def test_qwen_vl_inference(self, sample_image):
        """Test Qwen2-VL model inference."""
        model = ModelLoader.load_model("qwen_vl_2b")
        result = model.process_image(sample_image, "Describe this image")
        assert isinstance(result, str)
        ModelLoader.unload_model("qwen_vl_2b")

    @pytest.mark.skip(reason="Requires model download and GPU")
    def test_chat_functionality(self, sample_image):
        """Test chat functionality."""
        model = ModelLoader.load_model("qwen_vl_2b")
        response = model.chat(sample_image, "What do you see?")
        assert isinstance(response, str)
        assert len(response) > 0
        ModelLoader.unload_model("qwen_vl_2b")
