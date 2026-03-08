"""
Model Loader for ChatVLMLLM
Unified model loading with error recovery and GPU management
"""

import gc
import os
import time
from pathlib import Path
from typing import Dict, Optional

import yaml

from models.base_model import BaseModel
from models.dots_ocr_final import DotsOCRFinalModel
from models.got_ocr import GOTOCRModel
from models.qwen3_vl import Qwen3VLModel
from models.qwen_vl import QwenVLModel
from utils.logger import logger
from utils.model_cache import ModelCacheManager, check_model_availability

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, GPU features disabled")


class ModelLoader:
    """
    Model Loader — загрузка моделей с обработкой ошибок и GPU recovery.

    Возможности:
    1. Кэширование загруженных моделей
    2. Автоматическое восстановление GPU при ошибках CUDA
    3. Повтор загрузки при сбоях
    4. Поддержка конфигурации через config.yaml
    """

    # Registry of available models
    MODEL_REGISTRY: Dict[str, type] = {
        "got_ocr": GOTOCRModel,
        "qwen_vl_2b": QwenVLModel,
        "qwen3_vl_2b": Qwen3VLModel,
        "dots_ocr": DotsOCRFinalModel,
        "dots_ocr_final": DotsOCRFinalModel,
    }

    # Cache for loaded model instances
    _loaded_models: Dict[str, BaseModel] = {}

    # Cache manager
    _cache_manager = ModelCacheManager()

    @classmethod
    def _cuda_recovery(cls):
        """Восстановление CUDA состояния при ошибках."""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return

        try:
            logger.info("Recovering CUDA state...")

            torch.cuda.empty_cache()
            torch.cuda.synchronize()

            for i in range(torch.cuda.device_count()):
                with torch.cuda.device(i):
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()

            for _ in range(3):
                gc.collect()
                time.sleep(0.1)

            logger.info("CUDA state recovered")

        except Exception as e:
            logger.error(f"CUDA recovery failed: {e}")

    @classmethod
    def _apply_safe_defaults(cls, model_config: dict) -> dict:
        """Применение безопасных настроек к конфигурации модели."""
        config = cls.load_config()
        emergency = config.get("emergency_mode", {})

        if emergency.get("enabled", False):
            model_config["attn_implementation"] = "eager"
            model_config["use_flash_attention"] = False
            model_config["load_in_8bit"] = False
            model_config["load_in_4bit"] = False
            model_config["torch_dtype"] = "float16"
            logger.info("Emergency mode active — safe defaults applied")

        model_config.setdefault("device_map", "auto")
        model_config.setdefault("trust_remote_code", True)

        return model_config

    @classmethod
    def load_config(cls) -> dict:
        """Load configuration from YAML file."""
        config_path = Path("config.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @classmethod
    def _get_models_section(cls, config: dict) -> dict:
        """Return the active models section (transformers: preferred, models: as fallback).

        An empty or missing transformers section falls back to models:.
        """
        return config.get("transformers") or config.get("models", {})

    @classmethod
    def check_model_cache(cls, model_key: str) -> tuple[bool, Optional[str]]:
        """Check if model is in cache."""
        config = cls.load_config()

        models_config = cls._get_models_section(config)
        if model_key not in models_config:
            return False, f"Model '{model_key}' not found in config"

        model_config = models_config[model_key]
        model_path = model_config.get("model_path")

        if not model_path:
            return False, "No model_path in config"

        return check_model_availability(model_path)

    @classmethod
    def get_available_vram(cls) -> float:
        """Get available GPU VRAM in GB."""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return 0.0

        try:
            props = torch.cuda.get_device_properties(0)
            total_vram = props.total_memory / (1024**3)
            reserved = torch.cuda.memory_reserved(0) / (1024**3)
            available = total_vram - reserved

            logger.info(
                f"GPU VRAM: {total_vram:.2f}GB total, "
                f"{reserved:.2f}GB reserved, "
                f"{available:.2f}GB available"
            )
            return available
        except Exception as e:
            logger.warning(f"Failed to get VRAM info: {e}")
            return 0.0

    @classmethod
    def load_model(
        cls,
        model_key: str,
        force_reload: bool = False,
        precision: str = "auto",
        max_retries: int = 3,
        **kwargs,
    ) -> BaseModel:
        """
        Load a model with error handling and retry logic.

        Args:
            model_key: Model identifier from config
            force_reload: Force reload even if cached
            precision: Model precision (auto uses config)
            max_retries: Maximum number of loading attempts
            **kwargs: Additional arguments for model initialization

        Returns:
            Loaded model instance

        Raises:
            ValueError: If model key is not found
            RuntimeError: If model fails to load after all retries
        """
        # Check if already loaded
        if not force_reload and model_key in cls._loaded_models:
            logger.info(f"Using cached model instance: {model_key}")
            return cls._loaded_models[model_key]

        # Check if model class exists
        if model_key not in cls.MODEL_REGISTRY:
            available = ", ".join(cls.MODEL_REGISTRY.keys())
            raise ValueError(f"Model '{model_key}' not found. Available: {available}")

        # Load configuration
        config = cls.load_config()
        models_config = cls._get_models_section(config)

        if model_key not in models_config:
            raise ValueError(f"Model '{model_key}' not found in config.yaml")

        model_config = models_config[model_key].copy()

        # Apply safe defaults
        model_config = cls._apply_safe_defaults(model_config)

        # Override precision if specified
        if precision != "auto":
            model_config["precision"] = precision

        # Check cache status
        is_cached, cache_msg = cls.check_model_cache(model_key)
        if is_cached:
            logger.info(f"Model found in cache: {cache_msg}")
        else:
            logger.warning(f"Model not in cache: {cache_msg}")

        # Get model class
        model_class = cls.MODEL_REGISTRY[model_key]

        # Merge config with kwargs
        init_kwargs = {**model_config, **kwargs}

        # Loading with retries
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Loading model (attempt {attempt + 1}/{max_retries}): "
                    f"{model_key} [{model_config.get('model_path')}]"
                )

                # CUDA recovery before each attempt
                cls._cuda_recovery()

                # Initialize and load model
                model = model_class(config=init_kwargs)
                model.load_model()

                # Cache the instance
                cls._loaded_models[model_key] = model

                logger.info(f"Successfully loaded model: {model_key}")
                return model

            except RuntimeError as e:
                error_str = str(e)
                last_error = e

                if "CUDA error" in error_str:
                    logger.error(f"CUDA error (attempt {attempt + 1}): {e}")
                    cls._cuda_recovery()
                    time.sleep(2)
                elif "FlashAttention" in error_str or "flash_attn" in error_str:
                    logger.error(f"Flash Attention error (attempt {attempt + 1}): {e}")
                    init_kwargs["use_flash_attention"] = False
                    init_kwargs["attn_implementation"] = "eager"
                else:
                    logger.error(f"Loading error (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)

        raise RuntimeError(
            f"Failed to load model '{model_key}' after {max_retries} attempts. "
            f"Last error: {last_error}"
        )

    @classmethod
    def unload_model(cls, model_key: str) -> bool:
        """Unload a model from memory."""
        if model_key in cls._loaded_models:
            try:
                model = cls._loaded_models[model_key]
                if hasattr(model, "unload"):
                    model.unload()
                del cls._loaded_models[model_key]

                cls._cuda_recovery()

                logger.info(f"Unloaded model: {model_key}")
                return True
            except Exception as e:
                logger.error(f"Failed to unload model '{model_key}': {e}")
                return False
        return False

    @classmethod
    def unload_all_models(cls) -> None:
        """Unload all models from memory."""
        model_keys = list(cls._loaded_models.keys())
        for model_key in model_keys:
            cls.unload_model(model_key)

        cls._cuda_recovery()
        logger.info("All models unloaded")

    @classmethod
    def get_loaded_models(cls) -> list[str]:
        """Get list of currently loaded models."""
        return list(cls._loaded_models.keys())

    @classmethod
    def get_available_models(cls) -> list[dict]:
        """Get list of all models registered in MODEL_REGISTRY with metadata from config.

        Returns a list of dicts, each containing at least ``id`` and any
        additional fields present in config.yaml (name, model_path, params,
        precision).  This preserves the /models API response format that
        clients expect.
        """
        try:
            config = cls.load_config()
            models_config = cls._get_models_section(config)
        except Exception:
            models_config = {}

        result: list[dict] = []
        for model_key in cls.MODEL_REGISTRY:
            entry: dict = {"id": model_key}
            mc = models_config.get(model_key, {})
            for field in ("name", "model_path", "params", "precision"):
                if field in mc:
                    entry[field] = mc[field]
            result.append(entry)
        return result

    @classmethod
    def is_model_loaded(cls, model_key: str) -> bool:
        """Check if model is loaded."""
        return model_key in cls._loaded_models
