"""
ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ РЕАЛИЗАЦИЯ dots.ocr

Основано на глубоком изучении официальной документации и примеров.
Ключевые исправления:
1. Правильная обработка изображений (14x14 patches)
2. Корректные промпты для разных задач
3. Правильная обработка результатов
4. Устранение проблем с генерацией
5. Интеграция с XML-парсером таблиц
"""

import json
import os
import sys
import traceback
from typing import Any, Dict, List, Optional, Union

import torch
from PIL import Image

from models.base_model import BaseModel
from utils.logger import logger

# Импорт парсера XML-таблиц
try:
    from utils.table_parser import XMLTableParser, analyze_ocr_output
    from utils.table_renderer import format_ocr_result

    XML_PROCESSOR_AVAILABLE = True
except ImportError:
    XML_PROCESSOR_AVAILABLE = False
    logger.warning("XML processor not available")


class DotsOCRModel(BaseModel):
    """Финальная исправленная реализация dots.ocr."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = None
        self.processor = None
        self.max_new_tokens = config.get(
            "max_new_tokens", 2048
        )  # Уменьшено для стабильности

        # Инициализация XML-парсера
        if XML_PROCESSOR_AVAILABLE:
            self.xml_parser = XMLTableParser()
        else:
            self.xml_parser = None

        # Настройки обработки XML
        self.process_xml_tables = config.get("process_xml_tables", True)
        self.extract_structured_fields = config.get("extract_structured_fields", True)

        # Отключаем параллелизм токенизатора
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        # Официальные промпты из документации dots.ocr
        self.prompts = {
            # Простое извлечение текста
            "text_extraction": "Extract all text from this image.",
            # OCR с сохранением порядка чтения
            "ocr_reading_order": "Please extract all text content from this image while maintaining the original reading order.",
            # Структурированное извлечение (упрощенная версия)
            "structured_simple": "Extract the text content from this document image. Focus on the main text elements.",
            # Для таблиц
            "table_extraction": "Extract the table content from this image and format it as plain text.",
            # Минимальный промпт
            "minimal": "What text do you see?",
        }

    def load_model(self) -> None:
        """Загружаем модель с оптимизированными настройками."""
        try:
            logger.info(f"Loading dots.ocr from {self.model_path}")

            from transformers import AutoModelForCausalLM, AutoProcessor

            device = self._get_device()
            logger.info(f"Using device: {device}")

            # Базовые параметры загрузки
            load_kwargs = self._get_load_kwargs()

            # Оптимизированные параметры для dots.ocr
            load_kwargs.update(
                {
                    "torch_dtype": torch.float16,  # Используем float16 вместо bfloat16
                    "trust_remote_code": True,
                    "attn_implementation": "eager",  # Безопасный режим
                    "low_cpu_mem_usage": True,
                    "use_safetensors": True,
                }
            )

            # Загружаем модель
            logger.info("Loading model weights...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path, **load_kwargs
            )

            # Загружаем процессор
            logger.info("Loading processor...")
            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                use_fast=False,  # Используем медленный процессор для стабильности
            )

            # Устанавливаем модель в режим eval
            self.model.eval()

            # Проверяем токенизатор
            if hasattr(self.processor, "tokenizer"):
                if self.processor.tokenizer.pad_token is None:
                    self.processor.tokenizer.pad_token = (
                        self.processor.tokenizer.eos_token
                    )
                    logger.info("Set pad_token to eos_token")

            logger.info("dots.ocr loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load dots.ocr: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Предобработка изображения для dots.ocr."""
        try:
            # Конвертируем в RGB если нужно
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Оптимальный размер для dots.ocr (на основе документации)
            # dots.ocr работает с патчами 14x14, оптимальные размеры кратны 14
            max_size = 1400  # 100 * 14

            # Изменяем размер если изображение слишком большое
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                # Делаем размеры кратными 14
                new_size = (
                    ((new_size[0] + 13) // 14) * 14,
                    ((new_size[1] + 13) // 14) * 14,
                )
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image to {new_size}")

            return image

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image

    def _safe_generate(self, inputs: Dict, prompt_type: str = "simple") -> str:
        """Безопасная генерация с обработкой ошибок."""
        try:
            # Параметры генерации оптимизированные для dots.ocr
            generation_kwargs = {
                "max_new_tokens": min(
                    self.max_new_tokens, 1024
                ),  # Ограничиваем для стабильности
                "do_sample": False,  # Детерминированная генерация
                "temperature": 0.1,
                "pad_token_id": self.processor.tokenizer.eos_token_id,
                "eos_token_id": self.processor.tokenizer.eos_token_id,
                "use_cache": True,
                "output_attentions": False,
                "output_hidden_states": False,
            }

            # Для простых промптов используем меньше токенов
            if prompt_type in ["minimal", "text_extraction"]:
                generation_kwargs["max_new_tokens"] = 256

            # Генерируем ответ
            with torch.no_grad():
                generated_ids = self.model.generate(**inputs, **generation_kwargs)

            # Декодируем результат
            generated_ids_trimmed = [
                out_ids[len(in_ids) :]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            output_text = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            )[0]

            return output_text.strip()

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def _create_messages(self, image: Image.Image, prompt: str) -> List[Dict]:
        """Создаем сообщения в правильном формате для dots.ocr."""
        return [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

    def _process_with_prompt(
        self, image: Image.Image, prompt: str, prompt_type: str = "simple"
    ) -> str:
        """Обрабатываем изображение с заданным промптом."""
        try:
            # Предобрабатываем изображение
            processed_image = self._preprocess_image(image)

            # Создаем сообщения
            messages = self._create_messages(processed_image, prompt)

            # Применяем шаблон чата
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

            # Обрабатываем визуальную информацию
            try:
                from qwen_vl_utils import process_vision_info

                image_inputs, video_inputs = process_vision_info(messages)
            except ImportError:
                logger.warning("qwen_vl_utils не найден, используем прямую обработку")
                image_inputs = [processed_image]
                video_inputs = None

            # Подготавливаем входные данные
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )

            # Перемещаем на устройство
            device = next(self.model.parameters()).device
            inputs = inputs.to(device)

            # Генерируем ответ
            output_text = self._safe_generate(inputs, prompt_type)

            return output_text

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"[Processing error: {e}]"

    def process_image(
        self,
        image: Image.Image,
        prompt: Optional[str] = None,
        mode: str = "text_extraction",
        process_xml: bool = None,
    ) -> Union[str, Dict[str, Any]]:
        """Основной метод обработки изображения с поддержкой XML-таблиц."""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        try:
            # Выбираем промпт
            if prompt is None:
                prompt = self.prompts.get(mode, self.prompts["text_extraction"])

            logger.info(f"Processing with mode: {mode}")

            # Валидируем изображение
            if image is None:
                raise ValueError("Image is None")

            # Обрабатываем изображение
            result = self._process_with_prompt(image, prompt, mode)

            # Проверяем результат
            if not result or result.strip() == "":
                logger.warning("Empty result, trying alternative prompt")
                # Пробуем минимальный промпт
                result = self._process_with_prompt(
                    image, self.prompts["minimal"], "minimal"
                )

            # Определяем, нужно ли обрабатывать XML
            if process_xml is None:
                process_xml = self.process_xml_tables

            # Обработка XML-таблиц если включена
            if (
                XML_PROCESSOR_AVAILABLE
                and process_xml
                and result
                and ("<table" in result.lower() or "<tr" in result.lower())
            ):

                logger.info("Processing XML tables in output")
                processed_data = analyze_ocr_output(result)

                # Возвращаем структурированные данные для режимов с XML
                if mode in [
                    "table_extraction",
                    "structured_simple",
                    "document_parsing",
                ]:
                    return processed_data

            logger.info("Processing completed successfully")

            return result if result else "[dots.ocr: No text detected]"

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return f"[dots.ocr error: {e}]"

    def extract_text(self, image: Image.Image) -> str:
        """Извлекаем только текст без XML-обработки."""
        return self.process_image(image, mode="text_extraction", process_xml=False)

    def extract_text_with_xml(self, image: Image.Image) -> Union[str, Dict[str, Any]]:
        """Извлекаем текст с XML-обработкой."""
        return self.process_image(image, mode="text_extraction", process_xml=True)

    def get_raw_text(self, image: Image.Image) -> str:
        """Получить сырой текст без какой-либо обработки."""
        return self.process_image(image, mode="text_extraction", process_xml=False)

    def chat(self, image: Image.Image, prompt: str, **kwargs) -> str:
        """Чат с моделью."""
        return self.process_image(image, prompt=prompt, mode="custom")

    def extract_table(self, image: Image.Image) -> Union[str, Dict[str, Any]]:
        """Извлекаем содержимое таблицы с XML-обработкой."""
        return self.process_image(image, mode="table_extraction")

    def parse_document(self, image: Image.Image) -> Dict[str, Any]:
        """Парсим документ с поддержкой XML-таблиц."""
        try:
            # Используем структурированное извлечение
            result = self.process_image(image, mode="structured_simple")

            # Если результат уже структурирован (содержит XML-таблицы)
            if isinstance(result, dict):
                return {
                    "success": True,
                    "structured_data": result,
                    "method": "xml_table_parsing",
                }

            # Иначе возвращаем простой результат
            return {"success": True, "text": result, "method": "simplified_parsing"}

        except Exception as e:
            return {"success": False, "error": str(e), "method": "error"}

    def extract_payment_document(self, image: Image.Image) -> Dict[str, Any]:
        """Специализированное извлечение данных платежного документа."""
        try:
            # Используем специальный промпт для платежных документов
            payment_prompt = """Извлеки все данные из платежного документа в формате XML-таблицы. 
            Включи все реквизиты: ИНН, КПП, БИК, номера счетов, название организации, банк получателя."""

            result = self.process_image(
                image, prompt=payment_prompt, mode="document_parsing"
            )

            if isinstance(result, dict):
                # Добавляем специфичную для платежей информацию
                result["document_type"] = "payment_document"
                return result

            # Если XML не обнаружен, пытаемся извлечь поля вручную
            if XML_PROCESSOR_AVAILABLE:
                processed = analyze_ocr_output(result)
                processed["document_type"] = "payment_document"
                return processed

            return {
                "success": True,
                "text": result,
                "document_type": "payment_document",
                "method": "text_extraction",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "document_type": "payment_document",
            }

    def get_formatted_result(
        self, image: Image.Image, format_type: str = "mixed"
    ) -> str:
        """
        Получить отформатированный результат

        Args:
            image: Изображение для обработки
            format_type: Тип форматирования ('mixed', 'clean', 'markdown', 'payment')

        Returns:
            Отформатированный текст
        """
        # Получаем сырой результат
        raw_result = self.process_image(image, process_xml=False)

        # Форматируем если доступен форматировщик
        if XML_PROCESSOR_AVAILABLE:
            return format_ocr_result(raw_result, format_type)
        else:
            return raw_result

    def get_copyable_text(self, image: Image.Image) -> str:
        """Получить текст, удобный для копирования (без XML)"""
        return self.get_formatted_result(image, "clean")

    def get_structured_result(self, image: Image.Image) -> Dict[str, Any]:
        """Получить структурированный результат с XML-обработкой"""
        return self.process_image(image, mode="structured_simple", process_xml=True)


# Backward compatibility alias
DotsOCRFinalModel = DotsOCRModel
