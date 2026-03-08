"""Tests for model integration."""

import pytest
from PIL import Image
import numpy as np
from pathlib import Path

from models import ModelLoader
from models.base_model import BaseModel


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    # Create a simple image with text
    img_array = np.ones((100, 200, 3), dtype=np.uint8) * 255
    return Image.fromarray(img_array)


@pytest.fixture
def config_path():
    """Get path to test config."""
    return "config.yaml"


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
    
    def test_model_configuration(self, config_path):
        """Test model configuration structure."""
        config = ModelLoader.load_config()
        models_section = ModelLoader._get_models_section(config)
        for model_key, model_config in models_section.items():
            assert "name" in model_config
            assert "model_path" in model_config
            assert "precision" in model_config
    
    @pytest.mark.skip(reason="Requires model download and GPU")
    def test_load_model(self, config_path):
        """Test model loading (requires GPU and downloads)."""
        model = ModelLoader.load_model("got_ocr")
        assert model is not None
        assert isinstance(model, BaseModel)
        ModelLoader.unload_model("got_ocr")
    
    def test_model_caching(self):
        """Test that loaded models are cached."""
        loaded = ModelLoader.get_loaded_models()
        assert isinstance(loaded, list)


class TestBaseModel:
    """Tests for BaseModel class."""
    
    def test_device_detection(self):
        """Test device detection logic."""
        # This is a basic test that doesn't require GPU
        from models.base_model import BaseModel
        import torch
        
        # Mock a model instance
        class MockModel(BaseModel):
            def load_model(self):
                pass
            
            def process_image(self, image, prompt=None):
                return "test"
        
        model = MockModel({"model_path": "test", "precision": "fp16"})
        assert model.device in ["cuda", "mps", "cpu"]
    
    def test_extract_fields_basic(self):
        """Test basic field extraction."""
        from models.base_model import BaseModel
        
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
