"""Comprehensive mocked tests for all 4 model subclasses.

Tests cover load_model(), process_image(), inference(), and unload() for:
- Qwen3VLModel
- DotsOCRModel
- QwenVLModel
- GOTOCRModel

All model loads and GPU calls are mocked — no actual downloads or GPU required.
"""

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from models.base_model import BaseModel
from models.dots_ocr import DotsOCRModel
from models.got_ocr import GOTOCRModel
from models.qwen3_vl import Qwen3VLModel
from models.qwen_vl import QwenVLModel

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img_array = np.ones((100, 200, 3), dtype=np.uint8) * 255
    return Image.fromarray(img_array)


# ---------------------------------------------------------------------------
# TestQwen3VLModel
# ---------------------------------------------------------------------------


class TestQwen3VLModel:
    """Mocked tests for Qwen3VLModel."""

    def _make_cfg(self, **kwargs):
        base = {"model_path": "test/qwen3-vl", "precision": "fp16", "name": "qwen3vl"}
        base.update(kwargs)
        return base

    # 1. __init__ defaults
    def test_init_defaults(self):
        model = Qwen3VLModel(self._make_cfg())
        assert model.model_path == "test/qwen3-vl"
        assert model.precision == "fp16"
        assert model.min_pixels == 256
        assert model.max_pixels == 1280
        assert model.model is None
        assert model.processor is None

    def test_init_custom_pixels(self):
        model = Qwen3VLModel(self._make_cfg(min_pixels=128, max_pixels=640))
        assert model.min_pixels == 128
        assert model.max_pixels == 640

    # 2. load_model() with mocked transformers
    def test_load_model_sets_model_and_processor(self):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()
        transformers_mock = sys.modules["transformers"]
        transformers_mock.Qwen3VLForConditionalGeneration.from_pretrained.return_value = (
            mock_model_instance
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = (
            mock_processor_instance
        )

        model = Qwen3VLModel(self._make_cfg())
        model.load_model()

        assert model.model is mock_model_instance
        assert model.processor is mock_processor_instance
        mock_model_instance.eval.assert_called_once()

    def test_load_model_calls_from_pretrained_with_path(self):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()
        transformers_mock = sys.modules["transformers"]
        transformers_mock.Qwen3VLForConditionalGeneration.from_pretrained.return_value = (
            mock_model_instance
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = (
            mock_processor_instance
        )

        model = Qwen3VLModel(self._make_cfg())
        model.load_model()

        call_args = transformers_mock.AutoProcessor.from_pretrained.call_args
        assert call_args[0][0] == "test/qwen3-vl"
        model_call_args = (
            transformers_mock.Qwen3VLForConditionalGeneration.from_pretrained.call_args
        )
        assert model_call_args[0][0] == "test/qwen3-vl"

    # 3. process_image() with mocked model
    def test_process_image_returns_string(self, sample_image):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_inputs = MagicMock()
        mock_inputs.input_ids = [[1, 2, 3]]
        mock_inputs.to.return_value = mock_inputs
        mock_processor_instance.apply_chat_template.return_value = mock_inputs
        mock_model_instance.generate.return_value = [[1, 2, 3, 4, 5]]
        mock_model_instance.parameters.return_value = iter([MagicMock(device="cpu")])
        mock_processor_instance.batch_decode.return_value = ["extracted text"]

        model = Qwen3VLModel(self._make_cfg())
        model.model = mock_model_instance
        model.processor = mock_processor_instance

        result = model.process_image(sample_image, "Describe this image")
        assert isinstance(result, str)
        assert result == "extracted text"

    def test_process_image_raises_when_model_not_loaded(self, sample_image):
        model = Qwen3VLModel(self._make_cfg())
        with pytest.raises(RuntimeError, match="Model not loaded"):
            model.process_image(sample_image)

    # 4. unload() cycle
    def test_unload_sets_model_to_none(self):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()
        transformers_mock = sys.modules["transformers"]
        transformers_mock.Qwen3VLForConditionalGeneration.from_pretrained.return_value = (
            mock_model_instance
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = (
            mock_processor_instance
        )

        model = Qwen3VLModel(self._make_cfg())
        model.load_model()
        assert model.model is not None
        model.unload()
        assert model.model is None
        assert model.processor is None

    # 5. Full pipeline: load → run → unload
    def test_full_pipeline(self, sample_image):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_inputs = MagicMock()
        mock_inputs.input_ids = [[1, 2, 3]]
        mock_inputs.to.return_value = mock_inputs
        mock_processor_instance.apply_chat_template.return_value = mock_inputs
        mock_model_instance.generate.return_value = [[1, 2, 3, 4]]
        mock_model_instance.parameters.return_value = iter([MagicMock(device="cpu")])
        mock_processor_instance.batch_decode.return_value = ["hello world"]

        transformers_mock = sys.modules["transformers"]
        transformers_mock.Qwen3VLForConditionalGeneration.from_pretrained.return_value = (
            mock_model_instance
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = (
            mock_processor_instance
        )

        model = Qwen3VLModel(self._make_cfg())
        model.load_model()
        result = model.run(sample_image, "test prompt")
        assert isinstance(result, str)
        model.unload()
        assert model.model is None


# ---------------------------------------------------------------------------
# TestDotsOCRModel
# ---------------------------------------------------------------------------


class TestDotsOCRModel:
    """Mocked tests for DotsOCRModel."""

    def _make_cfg(self, **kwargs):
        base = {
            "model_path": "test/dots-ocr",
            "precision": "fp16",
            "name": "dots_ocr",
        }
        base.update(kwargs)
        return base

    # 1. __init__ defaults
    def test_init_defaults(self):
        model = DotsOCRModel(self._make_cfg())
        assert model.model_path == "test/dots-ocr"
        assert model.precision == "fp16"
        assert model.max_new_tokens == 2048
        assert model.model is None
        assert model.processor is None

    def test_init_custom_max_tokens(self):
        model = DotsOCRModel(self._make_cfg(max_new_tokens=512))
        assert model.max_new_tokens == 512

    # 2. load_model() with mocked transformers
    def test_load_model_sets_model_and_processor(self):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()
        mock_processor_instance.tokenizer.pad_token = None
        mock_processor_instance.tokenizer.eos_token = "<eos>"
        mock_processor_instance.tokenizer.eos_token_id = 2

        transformers_mock = sys.modules["transformers"]
        transformers_mock.AutoModelForCausalLM.from_pretrained.return_value = (
            mock_model_instance
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = (
            mock_processor_instance
        )

        model = DotsOCRModel(self._make_cfg())
        model.load_model()

        assert model.model is mock_model_instance
        assert model.processor is mock_processor_instance
        mock_model_instance.eval.assert_called_once()

    def test_load_model_calls_from_pretrained_with_path(self):
        mock_proc_instance = MagicMock()
        mock_proc_instance.tokenizer.pad_token = "pad"

        transformers_mock = sys.modules["transformers"]
        transformers_mock.AutoModelForCausalLM.from_pretrained.return_value = (
            MagicMock()
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = (
            mock_proc_instance
        )

        model = DotsOCRModel(self._make_cfg())
        model.load_model()

        assert (
            transformers_mock.AutoModelForCausalLM.from_pretrained.call_args[0][0]
            == "test/dots-ocr"
        )
        assert (
            transformers_mock.AutoProcessor.from_pretrained.call_args[0][0]
            == "test/dots-ocr"
        )

    # 3. process_image() with mocked model
    def test_process_image_returns_string(self, sample_image):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_inputs = MagicMock()
        mock_inputs.input_ids = [[1, 2, 3]]
        mock_inputs.to.return_value = mock_inputs
        mock_processor_instance.apply_chat_template.return_value = "chat text"
        mock_processor_instance.return_value = mock_inputs
        mock_processor_instance.tokenizer.eos_token_id = 2
        mock_model_instance.generate.return_value = [[1, 2, 3, 4]]
        mock_model_instance.parameters.return_value = iter([MagicMock(device="cpu")])
        mock_processor_instance.batch_decode.return_value = ["ocr result"]

        model = DotsOCRModel(self._make_cfg())
        model.model = mock_model_instance
        model.processor = mock_processor_instance

        result = model.process_image(sample_image)
        assert isinstance(result, str)

    def test_process_image_raises_when_model_not_loaded(self, sample_image):
        model = DotsOCRModel(self._make_cfg())
        with pytest.raises(RuntimeError, match="Model not loaded"):
            model.process_image(sample_image)

    def test_extract_text_calls_process_with_prompt(self, sample_image):
        model = DotsOCRModel(self._make_cfg())
        model.model = MagicMock()
        model.processor = MagicMock()

        with patch.object(model, "_process_with_prompt", return_value="text"):
            result = model.extract_text(sample_image)
        assert isinstance(result, str)

    def test_parse_document_returns_dict(self, sample_image):
        model = DotsOCRModel(self._make_cfg())
        model.model = MagicMock()
        model.processor = MagicMock()

        with patch.object(model, "process_image", return_value="document text"):
            result = model.parse_document(sample_image)
        assert isinstance(result, dict)
        assert "success" in result

    # 4. unload() cycle
    def test_unload_sets_model_to_none(self):
        mock_proc_instance = MagicMock()
        mock_proc_instance.tokenizer.pad_token = "pad"

        transformers_mock = sys.modules["transformers"]
        transformers_mock.AutoModelForCausalLM.from_pretrained.return_value = (
            MagicMock()
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = (
            mock_proc_instance
        )

        model = DotsOCRModel(self._make_cfg())
        model.load_model()
        assert model.model is not None
        model.unload()
        assert model.model is None
        assert model.processor is None

    # 5. Full pipeline: load → run → unload
    def test_full_pipeline(self, sample_image):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()
        mock_processor_instance.tokenizer.pad_token = "pad"

        transformers_mock = sys.modules["transformers"]
        transformers_mock.AutoModelForCausalLM.from_pretrained.return_value = (
            mock_model_instance
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = (
            mock_processor_instance
        )

        model = DotsOCRModel(self._make_cfg())
        model.load_model()

        with patch.object(model, "process_image", return_value="pipeline result"):
            result = model.run(sample_image, "prompt")
        assert isinstance(result, str)
        model.unload()
        assert model.model is None


# ---------------------------------------------------------------------------
# TestQwenVLModel
# ---------------------------------------------------------------------------


class TestQwenVLModel:
    """Mocked tests for QwenVLModel."""

    def _make_cfg(self, **kwargs):
        base = {
            "model_path": "test/qwen-vl",
            "precision": "fp16",
            "name": "qwen_vl",
        }
        base.update(kwargs)
        return base

    # 1. __init__ defaults
    def test_init_defaults(self):
        model = QwenVLModel(self._make_cfg())
        assert model.model_path == "test/qwen-vl"
        assert model.precision == "fp16"
        assert model.min_pixels == 256
        assert model.max_pixels == 1280
        assert model.model is None
        assert model.processor is None

    def test_init_custom_pixels(self):
        model = QwenVLModel(self._make_cfg(min_pixels=64, max_pixels=512))
        assert model.min_pixels == 64
        assert model.max_pixels == 512

    # 2. load_model() with mocked transformers
    def test_load_model_sets_model_and_processor(self):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        transformers_mock = sys.modules["transformers"]
        transformers_mock.Qwen2VLForConditionalGeneration.from_pretrained.return_value = (
            mock_model_instance
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = (
            mock_processor_instance
        )

        model = QwenVLModel(self._make_cfg())
        model.load_model()

        assert model.model is mock_model_instance
        assert model.processor is mock_processor_instance
        mock_model_instance.eval.assert_called_once()

    def test_load_model_calls_from_pretrained_with_path(self):
        transformers_mock = sys.modules["transformers"]
        transformers_mock.Qwen2VLForConditionalGeneration.from_pretrained.return_value = (
            MagicMock()
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = MagicMock()

        model = QwenVLModel(self._make_cfg())
        model.load_model()

        assert (
            transformers_mock.AutoProcessor.from_pretrained.call_args[0][0]
            == "test/qwen-vl"
        )
        assert (
            transformers_mock.Qwen2VLForConditionalGeneration.from_pretrained.call_args[
                0
            ][0]
            == "test/qwen-vl"
        )

    # 3. process_image() / chat() with mocked model
    def test_process_image_returns_string(self, sample_image):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_inputs = MagicMock()
        mock_inputs.input_ids = [[1, 2, 3]]
        mock_inputs.to.return_value = mock_inputs
        mock_processor_instance.apply_chat_template.return_value = "chat text"
        mock_processor_instance.return_value = mock_inputs
        mock_model_instance.generate.return_value = [[1, 2, 3, 4]]
        mock_model_instance.parameters.return_value = iter([MagicMock(device="cpu")])
        mock_processor_instance.batch_decode.return_value = ["qwen response"]

        # qwen_vl_utils.process_vision_info must return a 2-tuple
        sys.modules["qwen_vl_utils"].process_vision_info.return_value = (
            [sample_image],
            None,
        )

        model = QwenVLModel(self._make_cfg())
        model.model = mock_model_instance
        model.processor = mock_processor_instance

        result = model.process_image(sample_image, "Describe this")
        assert isinstance(result, str)
        assert result == "qwen response"

    def test_chat_raises_when_model_not_loaded(self, sample_image):
        model = QwenVLModel(self._make_cfg())
        with pytest.raises(RuntimeError, match="Model not loaded"):
            model.chat(sample_image, "hello")

    # 4. unload() cycle
    def test_unload_sets_model_to_none(self):
        transformers_mock = sys.modules["transformers"]
        transformers_mock.Qwen2VLForConditionalGeneration.from_pretrained.return_value = (
            MagicMock()
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = MagicMock()

        model = QwenVLModel(self._make_cfg())
        model.load_model()
        assert model.model is not None
        model.unload()
        assert model.model is None
        assert model.processor is None

    # 5. Full pipeline: load → run → unload
    def test_full_pipeline(self, sample_image):
        mock_model_instance = MagicMock()
        mock_processor_instance = MagicMock()

        mock_inputs = MagicMock()
        mock_inputs.input_ids = [[1, 2, 3]]
        mock_inputs.to.return_value = mock_inputs
        mock_processor_instance.apply_chat_template.return_value = "text"
        mock_processor_instance.return_value = mock_inputs
        mock_model_instance.generate.return_value = [[1, 2, 3, 4]]
        mock_model_instance.parameters.return_value = iter([MagicMock(device="cpu")])
        mock_processor_instance.batch_decode.return_value = ["pipeline output"]

        # qwen_vl_utils.process_vision_info must return a 2-tuple
        sys.modules["qwen_vl_utils"].process_vision_info.return_value = (
            [sample_image],
            None,
        )

        transformers_mock = sys.modules["transformers"]
        transformers_mock.Qwen2VLForConditionalGeneration.from_pretrained.return_value = (
            mock_model_instance
        )
        transformers_mock.AutoProcessor.from_pretrained.return_value = (
            mock_processor_instance
        )

        model = QwenVLModel(self._make_cfg())
        model.load_model()
        result = model.run(sample_image, "test prompt")
        assert isinstance(result, str)
        model.unload()
        assert model.model is None


# ---------------------------------------------------------------------------
# TestGOTOCRModel
# ---------------------------------------------------------------------------


class TestGOTOCRModel:
    """Mocked tests for GOTOCRModel."""

    def _make_cfg(self, **kwargs):
        base = {
            "model_path": "test/got-ocr",
            "precision": "fp16",
            "name": "got_ocr",
        }
        base.update(kwargs)
        return base

    # 1. __init__ defaults
    def test_init_defaults(self):
        model = GOTOCRModel(self._make_cfg())
        assert model.model_path == "test/got-ocr"
        assert model.precision == "fp16"
        assert model.ocr_type == "format"
        assert model.ocr_color == ""
        assert model.model is None
        assert model.tokenizer is None

    def test_init_custom_ocr_type(self):
        model = GOTOCRModel(self._make_cfg(ocr_type="ocr", ocr_color="red"))
        assert model.ocr_type == "ocr"
        assert model.ocr_color == "red"

    # 2. load_model() with mocked transformers
    def test_load_model_sets_model_and_tokenizer(self):
        mock_model_instance = MagicMock()
        mock_tokenizer_instance = MagicMock()

        transformers_mock = sys.modules["transformers"]
        transformers_mock.AutoModel.from_pretrained.return_value = mock_model_instance
        transformers_mock.AutoTokenizer.from_pretrained.return_value = (
            mock_tokenizer_instance
        )

        model = GOTOCRModel(self._make_cfg())
        model.load_model()

        assert model.model is mock_model_instance
        assert model.tokenizer is mock_tokenizer_instance
        mock_model_instance.eval.assert_called_once()

    def test_load_model_calls_from_pretrained_with_path(self):
        transformers_mock = sys.modules["transformers"]
        transformers_mock.AutoModel.from_pretrained.return_value = MagicMock()
        transformers_mock.AutoTokenizer.from_pretrained.return_value = MagicMock()

        model = GOTOCRModel(self._make_cfg())
        model.load_model()

        assert (
            transformers_mock.AutoTokenizer.from_pretrained.call_args[0][0]
            == "test/got-ocr"
        )
        assert (
            transformers_mock.AutoModel.from_pretrained.call_args[0][0]
            == "test/got-ocr"
        )

    # 3. process_image() with mocked model
    def test_process_image_returns_string(self, sample_image):
        mock_model_instance = MagicMock()
        mock_tokenizer_instance = MagicMock()
        mock_model_instance.chat.return_value = "ocr extracted text"

        model = GOTOCRModel(self._make_cfg())
        model.model = mock_model_instance
        model.tokenizer = mock_tokenizer_instance

        result = model.process_image(sample_image)
        assert isinstance(result, str)
        assert result == "ocr extracted text"

    def test_process_image_fallback_when_no_chat_method(self, sample_image):
        mock_model_instance = MagicMock(spec=[])  # no 'chat' attribute
        mock_tokenizer_instance = MagicMock()

        model = GOTOCRModel(self._make_cfg())
        model.model = mock_model_instance
        model.tokenizer = mock_tokenizer_instance

        result = model.process_image(sample_image)
        assert isinstance(result, str)

    def test_process_image_raises_when_model_not_loaded(self, sample_image):
        model = GOTOCRModel(self._make_cfg())
        with pytest.raises(RuntimeError, match="Model not loaded"):
            model.process_image(sample_image)

    # 4. unload() cycle
    def test_unload_sets_model_and_tokenizer_to_none(self):
        transformers_mock = sys.modules["transformers"]
        transformers_mock.AutoModel.from_pretrained.return_value = MagicMock()
        transformers_mock.AutoTokenizer.from_pretrained.return_value = MagicMock()

        model = GOTOCRModel(self._make_cfg())
        model.load_model()
        assert model.model is not None
        assert model.tokenizer is not None
        model.unload()
        assert model.model is None
        assert model.tokenizer is None

    # 5. Full pipeline: load → run → unload
    def test_full_pipeline(self, sample_image):
        mock_model_instance = MagicMock()
        mock_tokenizer_instance = MagicMock()
        mock_model_instance.chat.return_value = "full pipeline result"

        transformers_mock = sys.modules["transformers"]
        transformers_mock.AutoModel.from_pretrained.return_value = mock_model_instance
        transformers_mock.AutoTokenizer.from_pretrained.return_value = (
            mock_tokenizer_instance
        )

        model = GOTOCRModel(self._make_cfg())
        model.load_model()
        result = model.run(sample_image, "extract text")
        assert isinstance(result, str)
        model.unload()
        assert model.model is None


# ---------------------------------------------------------------------------
# TestBaseModelExtra — additional BaseModel coverage
# ---------------------------------------------------------------------------


class TestBaseModelExtra:
    """Additional coverage for BaseModel edge cases."""

    def _make_mock_model(self, **cfg_kwargs):
        """Create a concrete BaseModel subclass for testing."""

        class _M(BaseModel):
            def load_model(self):
                pass

            def process_image(self, image, prompt=None):
                return "result"

        defaults = {"model_path": "test/path", "precision": "fp16"}
        defaults.update(cfg_kwargs)
        return _M(defaults)

    # 1. int4 quantization path
    def test_get_load_kwargs_int4_has_quantization_config(self):
        """_get_load_kwargs returns quantization_config key for int4 on CUDA."""
        import torch

        with patch("models.base_model.torch.cuda.is_available", return_value=True):

            class _M(BaseModel):
                def load_model(self):
                    pass

                def process_image(self, image, prompt=None):
                    return ""

            mock_bnb_config = MagicMock(name="bnb_config")
            with patch("transformers.BitsAndBytesConfig", return_value=mock_bnb_config):
                m = _M({"model_path": "x", "precision": "int4"})
                kwargs = m._get_load_kwargs()

        assert "quantization_config" in kwargs

    # 2. _get_device GPU exception fallback to CPU
    def test_get_device_cuda_exception_fallback_to_cpu(self):
        """_get_device falls through to CPU when get_device_properties raises and MPS unavailable."""
        import torch

        with patch.object(torch.cuda, "is_available", return_value=True), patch.object(
            torch.cuda,
            "get_device_properties",
            side_effect=Exception("GPU error"),
        ), patch.object(torch.backends.mps, "is_available", return_value=False):

            class _M(BaseModel):
                def load_model(self):
                    pass

                def process_image(self, image, prompt=None):
                    return ""

            m = _M({"model_path": "x"})
            assert m.device == "cpu"

    def test_get_device_cuda_exception_fallback_to_mps(self):
        """_get_device falls through to MPS when CUDA raises and MPS available."""
        import torch

        with patch.object(torch.cuda, "is_available", return_value=True), patch.object(
            torch.cuda,
            "get_device_properties",
            side_effect=Exception("GPU init fail"),
        ), patch.object(torch.backends.mps, "is_available", return_value=True):

            class _M(BaseModel):
                def load_model(self):
                    pass

                def process_image(self, image, prompt=None):
                    return ""

            m = _M({"model_path": "x"})
            assert m.device == "mps"

    # 3. unload() with tokenizer
    def test_unload_clears_tokenizer(self):
        """unload() sets tokenizer to None."""
        model = self._make_mock_model()
        model.model = MagicMock()
        model.tokenizer = MagicMock()
        model.unload()
        assert model.tokenizer is None
        assert model.model is None

    # 4. unload() CUDA cleanup path
    def test_unload_calls_cuda_cleanup(self):
        """unload() calls torch.cuda.empty_cache and synchronize when CUDA available."""
        import torch

        model = self._make_mock_model()
        model.model = MagicMock()

        with patch.object(torch.cuda, "is_available", return_value=True), patch.object(
            torch.cuda, "empty_cache"
        ) as mock_empty, patch.object(torch.cuda, "synchronize") as mock_sync:
            model.unload()

        mock_empty.assert_called_once()
        mock_sync.assert_called_once()

    # 5. unload() exception in CUDA cleanup — should not propagate
    def test_unload_cuda_cleanup_exception_suppressed(self):
        """unload() does not propagate exceptions from CUDA cleanup."""
        import torch

        model = self._make_mock_model()
        model.model = MagicMock()

        with patch.object(torch.cuda, "is_available", return_value=True), patch.object(
            torch.cuda, "empty_cache", side_effect=RuntimeError("CUDA boom")
        ):
            # Should not raise
            model.unload()
        assert model.model is None

    # 6. unload() outer exception — should log warning, not crash
    def test_unload_outer_exception_suppressed(self):
        """unload() catches outer exceptions without crashing."""
        import torch

        model = self._make_mock_model()
        model.model = MagicMock()
        model.processor = MagicMock()

        # Make torch.cuda.is_available raise to trigger the outer except block
        with patch.object(
            torch.cuda,
            "is_available",
            side_effect=Exception("outer error"),
        ):
            # Should not raise — outer try/except in unload() catches it
            model.unload()
