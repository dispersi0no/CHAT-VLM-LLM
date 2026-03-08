"""Qwen2-VL model integration following official recommendations.

Official repository: https://github.com/QwenLM/Qwen2-VL
HuggingFace: https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct
              https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct

Recommended usage (from official docs):
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from qwen_vl_utils import process_vision_info

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        "Qwen/Qwen2-VL-2B-Instruct",
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")
"""

from typing import Any, Dict, List, Optional

import torch
from PIL import Image

from models.base_model import BaseModel
from utils.logger import logger


class QwenVLModel(BaseModel):
    """Qwen2-VL model for vision-language tasks following official recommendations."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Qwen2-VL model.

        Args:
            config: Model configuration dictionary
        """
        super().__init__(config)
        self.model = None
        self.processor = None

        # Qwen2-VL specific settings
        self.min_pixels = config.get("min_pixels", 256)
        self.max_pixels = config.get("max_pixels", 1280)

    def load_model(self) -> None:
        """Load Qwen2-VL model following official recommendations."""
        try:
            logger.info(f"Loading Qwen2-VL model from {self.model_path}")

            # Check if required packages are available
            try:
                from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
            except ImportError:
                raise ImportError(
                    "transformers library with Qwen2-VL support is required. "
                    "Install with: pip install transformers>=4.37.0"
                )

            # Determine device
            device = self._get_device()
            logger.info(f"Using device: {device}")

            # Load processor
            logger.info("Loading processor...")
            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                min_pixels=self.min_pixels * 28 * 28,
                max_pixels=self.max_pixels * 28 * 28,
            )

            # Build loading kwargs using base class method
            load_kwargs = self._get_load_kwargs()

            # Set precision (official recommendation: bfloat16 or float16)
            if not torch.cuda.is_available():
                # Force float32 on CPU for better compatibility
                load_kwargs["torch_dtype"] = torch.float32

            # ПРИНУДИТЕЛЬНО ОТКЛЮЧАЕМ Flash Attention для совместимости
            load_kwargs["attn_implementation"] = (
                "eager"  # Принудительно eager attention
            )

            # Убираем любые упоминания Flash Attention
            if "use_flash_attention" in load_kwargs:
                del load_kwargs["use_flash_attention"]

            # Load model
            logger.info("Loading model weights...")
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_path, **load_kwargs
            )

            # Set to eval mode
            self.model.eval()

            logger.info("Qwen2-VL model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Qwen2-VL model: {e}")
            raise

    def process_image(
        self, image: Image.Image, prompt: str = "Extract all text from this image"
    ) -> str:
        """Process image with default OCR prompt.

        Args:
            image: PIL Image to process
            prompt: OCR prompt (default: extract all text)

        Returns:
            Extracted text
        """
        return self.chat(image, prompt)

    def chat(
        self,
        image: Image.Image,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> str:
        """Chat with model about image following official API.

        Args:
            image: PIL Image
            prompt: User prompt
            history: Optional conversation history
            **kwargs: Additional generation arguments

        Returns:
            Model response
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            logger.info(f"Processing chat request: {prompt[:50]}...")

            # Prepare messages following official format
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": image,
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ]

            # Apply chat template
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            # Process inputs
            # Note: process_vision_info is from qwen_vl_utils (may need separate install)
            try:
                from qwen_vl_utils import process_vision_info

                image_inputs, video_inputs = process_vision_info(messages)
            except ImportError:
                # Fallback: basic processing
                image_inputs = [image]
                video_inputs = None

            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )

            # Move to device
            device = next(self.model.parameters()).device
            inputs = inputs.to(device)

            # Generate response
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=kwargs.get("max_new_tokens", 512),
                    temperature=kwargs.get("temperature", 0.7),
                    do_sample=True,
                )

            # Decode response
            generated_ids_trimmed = [
                out_ids[len(in_ids) :]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            response = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            logger.info("Chat response generated successfully")
            return response

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            raise

    def unload(self) -> None:
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            self.model = None

        if self.processor is not None:
            del self.processor
            self.processor = None

        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("Qwen2-VL model unloaded")
