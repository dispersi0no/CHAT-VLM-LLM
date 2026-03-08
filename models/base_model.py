"""Base class for VLM models."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import torch
from PIL import Image

from utils.logger import logger


class BaseModel(ABC):
    """Abstract base class for Vision Language Models."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize base VLM model.

        Args:
            config: Model configuration dictionary containing:
                - model_path: HuggingFace model identifier
                - precision: Model precision (fp16, bf16, int8, int4)
                - device_map: Device mapping strategy
        """
        self.config = config
        self.model_path = config.get("model_path", "")
        self.model_id = self.model_path  # Alias for compatibility
        self.model_name = config.get("name", self.model_path)  # Human-readable name
        self.precision = config.get("precision", "fp16")
        self.device_map = config.get("device_map", "auto")
        self.model = None
        self.processor = None
        self.device = self._get_device()

    def _get_device(self) -> str:
        """Determine optimal device for model inference - FORCE GPU USAGE."""
        # CRITICAL: Always prefer CUDA if available
        if torch.cuda.is_available():
            # Check if GPU has enough memory
            try:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(
                    f"GPU detected: {torch.cuda.get_device_name(0)} with {gpu_memory:.2f}GB VRAM"
                )
                return "cuda"
            except Exception as e:
                logger.warning(f"GPU detection failed: {e}, falling back to CPU")

        # Fallback to MPS on Apple Silicon
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"

        logger.warning("No GPU available, using CPU (will be very slow)")
        return "cpu"

    def _get_load_kwargs(self) -> dict:
        """Get loading kwargs with FORCED GPU usage."""
        load_kwargs = {
            "trust_remote_code": True,
        }

        # CRITICAL: Force GPU usage if available
        if torch.cuda.is_available():
            logger.info("FORCING GPU usage with device_map='auto'")
            load_kwargs["device_map"] = "auto"  # Force auto device mapping to GPU

            # GPU precision settings
            if self.precision == "fp16":
                load_kwargs["torch_dtype"] = torch.float16
            elif self.precision == "bf16":
                load_kwargs["torch_dtype"] = torch.bfloat16
            elif self.precision == "int8":
                load_kwargs["load_in_8bit"] = True
            elif self.precision == "int4":
                from transformers import BitsAndBytesConfig

                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
        else:
            # CPU fallback (will be slow)
            logger.warning("⚠️ NO GPU AVAILABLE - USING CPU (VERY SLOW)")
            load_kwargs["torch_dtype"] = torch.float32

        return load_kwargs

    @abstractmethod
    def load_model(self) -> None:
        """Load model and processor from HuggingFace."""
        pass

    @abstractmethod
    def process_image(self, image: Image.Image, prompt: Optional[str] = None) -> str:
        """
        Process image and return text output.

        Args:
            image: PIL Image object
            prompt: Optional prompt for the model

        Returns:
            Extracted text or model response
        """
        pass

    def extract_fields(self, text: str, fields: List[str]) -> Dict[str, str]:
        """
        Extract structured fields from text.

        Args:
            text: Raw text from OCR
            fields: List of field names to extract

        Returns:
            Dictionary mapping field names to extracted values
        """
        result = {}

        for field in fields:
            result[field] = self._extract_single_field(text, field)

        return result

    def _extract_single_field(self, text: str, field: str) -> str:
        """
        Extract single field from text.

        Args:
            text: Source text
            field: Field name to extract

        Returns:
            Extracted field value or empty string
        """
        lines = text.split("\n")
        field_lower = field.lower()

        for i, line in enumerate(lines):
            if field_lower in line.lower():
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        return parts[1].strip()
                elif i + 1 < len(lines):
                    return lines[i + 1].strip()

        return ""

    def run(self, image: Image.Image, prompt: Optional[str] = None, **kwargs) -> str:
        """
        Unified entry point for model inference.

        Replaces the scattered if/elif dispatch chains in api.py.
        Subclasses may override this method for model-specific routing
        (e.g. routing to ``extract_text`` or ``parse_document``).

        Routing logic:
        - If ``prompt`` and generation kwargs (temperature, max_new_tokens,
          etc.) are provided, delegates to :meth:`chat` so that subclass
          overrides receive those parameters.
        - Otherwise falls back to :meth:`process_image`.

        Args:
            image: PIL Image object
            prompt: Optional prompt / question for the model
            **kwargs: Additional keyword arguments forwarded to
                      :meth:`chat` (e.g. ``language``, ``temperature``,
                      ``max_new_tokens``).

        Returns:
            Model output text
        """
        if prompt and kwargs:
            return self.chat(image=image, message=prompt, **kwargs)
        return self.process_image(image, prompt)

    def chat(
        self,
        image: Image.Image,
        message: str,
        history: List[Dict[str, str]] = None,
        **kwargs,
    ) -> str:
        """
        Interactive chat with image context.

        Args:
            image: Context image
            message: User message
            history: Chat history
            **kwargs: Generation parameters (temperature, max_new_tokens,
                      top_p, etc.). Subclasses that support these should
                      extract and forward them to the underlying model.

        Returns:
            Model response
        """
        # Default implementation uses process_image
        # Override in subclasses for proper chat support
        return self.process_image(image, message)

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics."""
        return {
            "model_id": self.model_id,
            "device": self.device,
            "config": self.config,
            "loaded": self.model is not None,
        }

    def unload(self) -> None:
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
