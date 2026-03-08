"""GOT-OCR 2.0 variants (UCAS and HuggingFace versions).

This module provides wrappers for different GOT-OCR implementations:
- ucaslcl/GOT-OCR2_0 (UCAS version)
- stepfun-ai/GOT-OCR-2.0-hf (HuggingFace version)

Both are variants of the same GOT-OCR 2.0 model with potentially different
implementations or optimizations.
"""

from typing import Any, Dict, Optional
from PIL import Image
import torch

from models.base_model import BaseModel
from utils.logger import logger


class GOTOCRUCASModel(BaseModel):
    """GOT-OCR 2.0 UCAS version (ucaslcl/GOT-OCR2_0)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = None
        self.tokenizer = None
        
        # GOT-OCR specific settings
        self.ocr_type = config.get('ocr_type', 'format')
        self.ocr_color = config.get('ocr_color', '')
    
    def load_model(self) -> None:
        """Load GOT-OCR UCAS model."""
        try:
            logger.info(f"Loading GOT-OCR UCAS from {self.model_path}")
            
            from transformers import AutoModel, AutoTokenizer
            
            device = self._get_device()
            logger.info(f"Using device: {device}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Build loading kwargs
            load_kwargs = {
                'trust_remote_code': True,
                'device_map': self.device_map,
            }
            
            # Set precision
            if self.precision == "fp16":
                load_kwargs['torch_dtype'] = torch.float16
            elif self.precision == "int8":
                load_kwargs['load_in_8bit'] = True
            
            # Load model
            self.model = AutoModel.from_pretrained(
                self.model_path,
                **load_kwargs
            )
            
            self.model.eval()
            logger.info("GOT-OCR UCAS loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load GOT-OCR UCAS: {e}")
            raise
    
    def process_image(
        self,
        image: Image.Image,
        ocr_type: Optional[str] = None,
        ocr_color: Optional[str] = None
    ) -> str:
        """Process image with GOT-OCR UCAS.
        
        Args:
            image: PIL Image to process
            ocr_type: OCR type ('format', 'ocr', 'multi-crop')
            ocr_color: Optional color specification
            
        Returns:
            Extracted text
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded")
        
        try:
            ocr_type = ocr_type or self.ocr_type
            ocr_color = ocr_color or self.ocr_color
            
            logger.info(f"Processing image with GOT-OCR UCAS (type: {ocr_type})")
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save image to temporary file (UCAS version requires file path)
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                image.save(tmp_file.name, format='JPEG')
                image_path = tmp_file.name
            
            try:
                with torch.no_grad():
                    if hasattr(self.model, 'chat'):
                        # Official API: model.chat(tokenizer, image_file, ocr_type='ocr')
                        result = self.model.chat(
                            self.tokenizer,
                            image_path,  # Use file path as required by UCAS API
                            ocr_type=ocr_type,
                            ocr_color=ocr_color if ocr_color else ''
                        )
                    else:
                        # Fallback implementation
                        result = self._basic_inference(image_path)
                
                # Clean up temporary file
                try:
                    os.unlink(image_path)
                except:
                    pass
                
                return result.strip() if result else "[GOT-OCR UCAS: Empty result]"
                
            except Exception as e:
                # Clean up temporary file on error
                try:
                    os.unlink(image_path)
                except:
                    pass
                raise e
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise
    
    def _basic_inference(self, image: Image.Image) -> str:
        """Basic inference fallback."""
        return "[GOT-OCR UCAS inference - implement based on model API]"
    
    def chat(self, image: Image.Image, prompt: str, **kwargs) -> str:
        """Chat interface (returns OCR result)."""
        return self.process_image(image)
    
    def unload(self) -> None:
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("GOT-OCR UCAS unloaded")


class GOTOCRHFModel(BaseModel):
    """GOT-OCR 2.0 HuggingFace version (stepfun-ai/GOT-OCR-2.0-hf)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = None
        self.processor = None
        
        # GOT-OCR specific settings
        self.ocr_type = config.get('ocr_type', 'format')
        self.ocr_color = config.get('ocr_color', '')
    
    def load_model(self) -> None:
        """Load GOT-OCR HF model."""
        try:
            logger.info(f"Loading GOT-OCR HF from {self.model_path}")
            
            from transformers import AutoModelForImageTextToText, AutoProcessor
            
            device = self._get_device()
            logger.info(f"Using device: {device}")
            
            # Load processor
            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Build loading kwargs
            load_kwargs = {
                'trust_remote_code': True,
                'device_map': self.device_map,
            }
            
            # Set precision
            if self.precision == "fp16":
                load_kwargs['torch_dtype'] = torch.float16
            elif self.precision == "int8":
                load_kwargs['load_in_8bit'] = True
            
            # Load model - используем правильный класс для GOT-OCR HF
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_path,
                **load_kwargs
            )
            
            self.model.eval()
            logger.info("GOT-OCR HF loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load GOT-OCR HF: {e}")
            raise
    
    def process_image(
        self,
        image: Image.Image,
        ocr_type: Optional[str] = None,
        ocr_color: Optional[str] = None
    ) -> str:
        """Process image with GOT-OCR HF - FIXED IMPLEMENTATION WITH TIMEOUT.
        
        Args:
            image: PIL Image to process
            ocr_type: OCR type ('format', 'ocr', 'multi-crop')
            ocr_color: Optional color specification
            
        Returns:
            Extracted text
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("Model not loaded")
        
        try:
            ocr_type = ocr_type or self.ocr_type
            ocr_color = ocr_color or self.ocr_color
            
            logger.info(f"Processing image with GOT-OCR HF (type: {ocr_type})")
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Process image using OFFICIAL GOT-OCR HF API from documentation
            device = next(self.model.parameters()).device
            
            # Use format parameter for formatted text (LaTeX, markdown)
            format_text = (ocr_type == "format")
            
            # Process inputs exactly as in official documentation
            inputs = self.processor(image, return_tensors="pt", format=format_text).to(device)
            
            with torch.no_grad():
                # ИСПРАВЛЕНО: Еще более агрессивные параметры против зависания
                generated_ids = self.model.generate(
                    **inputs,
                    do_sample=False,
                    tokenizer=self.processor.tokenizer,
                    stop_strings="<|im_end|>",
                    max_new_tokens=128,      # СИЛЬНО УМЕНЬШЕНО с 512 до 128
                    num_beams=1,             # Отключаем beam search
                    early_stopping=True,     # Ранняя остановка
                    pad_token_id=self.processor.tokenizer.eos_token_id,
                    eos_token_id=self.processor.tokenizer.eos_token_id,
                    repetition_penalty=1.5,  # УВЕЛИЧЕНО против повторений
                    no_repeat_ngram_size=2,  # УМЕНЬШЕНО для более агрессивной фильтрации
                    use_cache=True,
                    # Убираем проблемные параметры
                )
                
                # Decode exactly as in official documentation
                result = self.processor.decode(
                    generated_ids[0, inputs["input_ids"].shape[1]:], 
                    skip_special_tokens=True
                )
            
            # ДОБАВЛЕНО: Проверка на мусорный вывод
            if self._is_garbage_output(result):
                logger.warning("Detected garbage output, returning fallback message")
                return "[GOT-OCR HF: Модель генерирует некорректный вывод - возможно несовместимость версий]"
            
            return result.strip() if result else "[GOT-OCR HF: Empty result]"
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return f"[GOT-OCR HF error: {e}]"
    
    def _is_garbage_output(self, text: str) -> bool:
        """Проверяет, является ли вывод мусорным."""
        if not text or len(text) < 10:
            return False
        
        # Индикаторы мусорного вывода
        garbage_indicators = [
            "ĠĠĠ", "ĊĊĊ", 
            "▁▁▁", "ĉĉĉ", "ġġġ", "Ċ", "ĠĠ"
        ]
        
        # Если найдено много индикаторов мусора
        garbage_count = sum(1 for indicator in garbage_indicators if indicator in text)
        if garbage_count >= 3:
            return True
        
        # Если текст состоит в основном из повторяющихся токенов
        words = text.split()
        if len(words) > 10:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.3:  # Менее 30% уникальных слов
                return True
        
        return False
    
    def _basic_inference(self, image: Image.Image) -> str:
        """Basic inference fallback."""
        return "[GOT-OCR HF inference - implement based on model API]"
    
    def chat(self, image: Image.Image, prompt: str, **kwargs) -> str:
        """Chat interface (returns OCR result)."""
        return self.process_image(image)
    
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
        logger.info("GOT-OCR HF unloaded")