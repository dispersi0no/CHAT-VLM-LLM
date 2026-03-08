"""GOT-OCR 2.0 model integration following official recommendations.

Official repository: https://github.com/Ucas-HaoranWei/GOT-OCR2.0
HuggingFace: https://huggingface.co/stepfun-ai/GOT-OCR2_0

Recommended usage:
    from transformers import AutoModel, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained('stepfun-ai/GOT-OCR2_0', trust_remote_code=True)
    model = AutoModel.from_pretrained('stepfun-ai/GOT-OCR2_0', trust_remote_code=True)
"""

from typing import Any, Dict, Optional

import torch
from PIL import Image

from models.base_model import BaseModel
from utils.logger import logger


class GOTOCRModel(BaseModel):
    """GOT-OCR 2.0 model for document OCR following official recommendations."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize GOT-OCR model.

        Args:
            config: Model configuration dictionary
        """
        super().__init__(config)

        # GOT-OCR specific settings
        self.ocr_type = config.get("ocr_type", "format")
        self.ocr_color = config.get("ocr_color", "")

    def load_model(self) -> None:
        """Load GOT-OCR model following official recommendations."""
        try:
            logger.info(f"Loading GOT-OCR model from {self.model_path}")

            # Check if transformers is available
            try:
                from transformers import AutoModel, AutoTokenizer
            except ImportError:
                raise ImportError(
                    "transformers library is required. Install with: "
                    "pip install transformers"
                )

            # Load tokenizer (official recommendation: trust_remote_code=True)
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path, trust_remote_code=True
            )

            # Determine device
            device = self._get_device()
            logger.info(f"Using device: {device}")

            # Load model (official recommendation: trust_remote_code=True)
            logger.info("Loading model weights...")

            # Build loading kwargs using base class method
            load_kwargs = self._get_load_kwargs()

            # Load model
            self.model = AutoModel.from_pretrained(self.model_path, **load_kwargs)

            # Set to eval mode
            self.model.eval()

            logger.info("GOT-OCR model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load GOT-OCR model: {e}")
            raise

    def process_image(
        self,
        image: Image.Image,
        ocr_type: Optional[str] = None,
        ocr_color: Optional[str] = None,
    ) -> str:
        """Process image and extract text using GOT-OCR.

        Args:
            image: PIL Image to process
            ocr_type: OCR type ('format', 'ocr', 'multi-crop')
            ocr_color: Optional color specification

        Returns:
            Extracted text
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            # Use provided parameters or defaults
            ocr_type = ocr_type or self.ocr_type
            ocr_color = ocr_color or self.ocr_color

            logger.info(f"Processing image with GOT-OCR (type: {ocr_type})")

            # Following official GOT-OCR usage:
            # result = model.chat(tokenizer, image_path, ocr_type=ocr_type)

            with torch.no_grad():
                # Note: This is a placeholder for actual GOT-OCR inference
                # The exact API depends on the model's chat() method
                if hasattr(self.model, "chat"):
                    result = self.model.chat(
                        self.tokenizer, image, ocr_type=ocr_type, ocr_color=ocr_color
                    )
                else:
                    # Fallback: basic inference
                    result = self._basic_inference(image)

            logger.info("Text extraction completed")
            return result

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise

    def _basic_inference(self, image: Image.Image) -> str:
        """Basic inference fallback."""
        # Placeholder for basic inference
        # This should be replaced with actual model-specific code
        return "[GOT-OCR inference placeholder - implement actual inference]"

    def chat(self, image: Image.Image, prompt: str, **kwargs) -> str:
        """Chat with model about image (if supported).

        Args:
            image: PIL Image
            prompt: User prompt
            **kwargs: Additional arguments

        Returns:
            Model response
        """
        # GOT-OCR is primarily for OCR, not general chat
        # Return OCR result with prompt context
        ocr_result = self.process_image(image)
        return f"OCR Result:\n{ocr_result}"
