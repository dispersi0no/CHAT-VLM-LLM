"""Qwen3-VL model integration following official recommendations.

Official: https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct
GitHub: https://github.com/QwenLM/Qwen3-VL

Qwen3-VL is the most powerful vision-language model in the Qwen series.
Key improvements over Qwen2-VL:
- Advanced OCR (32 languages)
- Visual agent capabilities
- 256K context (expandable to 1M)
- Enhanced spatial perception
- Better video understanding
"""

from typing import Any, Dict, List, Optional, Union

import torch
from PIL import Image

from models.base_model import BaseModel
from utils.logger import logger


class Qwen3VLModel(BaseModel):
    """Qwen3-VL vision-language model."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = None
        self.processor = None

        # Qwen3-VL specific settings
        self.min_pixels = config.get("min_pixels", 256)
        self.max_pixels = config.get("max_pixels", 1280)

    def load_model(self) -> None:
        """Load Qwen3-VL model."""
        try:
            logger.info(f"Loading Qwen3-VL from {self.model_path}")

            from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

            device = self._get_device()
            logger.info(f"Using device: {device}")

            # Load processor
            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                min_pixels=self.min_pixels * 28 * 28,
                max_pixels=self.max_pixels * 28 * 28,
            )

            # Build loading kwargs using base class method
            load_kwargs = self._get_load_kwargs()

            # Force float32 on CPU for better compatibility
            if not torch.cuda.is_available():
                load_kwargs["torch_dtype"] = torch.float32

            # ПРИНУДИТЕЛЬНО ОТКЛЮЧАЕМ Flash Attention для совместимости
            load_kwargs["attn_implementation"] = (
                "eager"  # Принудительно eager attention
            )

            # Убираем любые упоминания Flash Attention
            if "use_flash_attention" in load_kwargs:
                del load_kwargs["use_flash_attention"]

            # Load model with compatibility fixes
            logger.info("Loading model weights...")
            try:
                self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                    self.model_path, **load_kwargs
                )
            except AttributeError as attr_error:
                if "pad_token_id" in str(attr_error):
                    logger.warning("Fixing pad_token_id issue for Qwen3-VL...")
                    # Try loading with trust_remote_code and custom config
                    load_kwargs["trust_remote_code"] = True

                    # Load config first and fix it
                    from transformers import AutoConfig

                    config = AutoConfig.from_pretrained(
                        self.model_path, trust_remote_code=True
                    )

                    # Fix missing pad_token_id in text_config
                    if hasattr(config, "text_config") and not hasattr(
                        config.text_config, "pad_token_id"
                    ):
                        config.text_config.pad_token_id = (
                            config.text_config.eos_token_id
                            if hasattr(config.text_config, "eos_token_id")
                            else 0
                        )
                        logger.info(
                            f"Set pad_token_id to {config.text_config.pad_token_id}"
                        )

                    # Try loading with fixed config
                    self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                        self.model_path, config=config, **load_kwargs
                    )
                else:
                    raise attr_error

            self.model.eval()
            logger.info("Qwen3-VL loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Qwen3-VL: {e}")
            raise

    def process_image(
        self,
        image: Union[Image.Image, str],
        prompt: str = "Describe this image in detail.",
        **kwargs,
    ) -> str:
        """Process image with Qwen3-VL.

        Args:
            image: PIL Image or image URL
            prompt: Text prompt
            **kwargs: Additional generation parameters

        Returns:
            Model response
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        try:
            logger.info("Processing image with Qwen3-VL")

            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]

            # Apply chat template and tokenize
            inputs = self.processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
            )

            # Move to device
            device = next(self.model.parameters()).device
            inputs = inputs.to(device)

            # Generation parameters
            gen_kwargs = {
                "max_new_tokens": kwargs.get("max_new_tokens", 128),
                "do_sample": kwargs.get("do_sample", False),
            }

            if kwargs.get("temperature"):
                gen_kwargs["temperature"] = kwargs["temperature"]
            if kwargs.get("top_p"):
                gen_kwargs["top_p"] = kwargs["top_p"]
            if kwargs.get("top_k"):
                gen_kwargs["top_k"] = kwargs["top_k"]

            # Generate
            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, **gen_kwargs)

            # Decode
            generated_ids_trimmed = [
                out_ids[len(in_ids) :]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            output = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            logger.info("Processing completed")
            return output

        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    def chat(self, image: Union[Image.Image, str], prompt: str, **kwargs) -> str:
        """Chat with Qwen3-VL about image.

        Args:
            image: PIL Image or URL
            prompt: User question
            **kwargs: Generation parameters

        Returns:
            Model response
        """
        return self.process_image(image, prompt, **kwargs)

    def extract_text(
        self, image: Union[Image.Image, str], language: Optional[str] = None
    ) -> str:
        """Extract text from image using Qwen3-VL's enhanced OCR.

        Supports 32 languages with improved accuracy.

        Args:
            image: PIL Image or URL
            language: Optional language hint

        Returns:
            Extracted text
        """
        prompt = "Extract all text from this image. "
        if language:
            prompt += f"The text is in {language}. "
        prompt += "Maintain the original structure and formatting."

        return self.process_image(image, prompt, max_new_tokens=2048)

    def analyze_document(
        self, image: Union[Image.Image, str], focus: str = "general"
    ) -> str:
        """Analyze document with specific focus.

        Args:
            image: PIL Image or URL
            focus: Analysis focus (general, layout, content, tables)

        Returns:
            Analysis result
        """
        prompts = {
            "general": "Analyze this document and provide a comprehensive summary.",
            "layout": "Describe the layout and structure of this document.",
            "content": "Extract and summarize the main content of this document.",
            "tables": "Identify and extract all tables from this document in markdown format.",
        }

        prompt = prompts.get(focus, prompts["general"])
        return self.process_image(image, prompt, max_new_tokens=2048)

    def visual_reasoning(self, image: Union[Image.Image, str], question: str) -> str:
        """Perform visual reasoning on image.

        Args:
            image: PIL Image or URL
            question: Reasoning question

        Returns:
            Reasoning result
        """
        prompt = f"{question}\n\nThink step by step and provide detailed reasoning."
        return self.process_image(image, prompt, max_new_tokens=1024)

    def unload(self) -> None:
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.processor is not None:
            del self.processor
            self.processor = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Qwen3-VL unloaded")
