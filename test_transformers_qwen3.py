"""
Тест загрузки Qwen3-VL в режиме Transformers после исправления symlinks
"""

import os
import sys

# КРИТИЧЕСКИ ВАЖНО: Отключаем symlinks ПЕРЕД импортом
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'

import disable_symlinks_startup  # Автоматическое отключение symlinks

from models.model_loader import ModelLoader
from utils.logger import logger
from PIL import Image
import io
import base64

def create_test_image():
    """Создание тестового изображения"""
    img = Image.new('RGB', (200, 100), color='white')
    return img

def test_qwen3_loading():
    """Тест загрузки модели Qwen3-VL"""
    
    logger.info("=" * 80)
    logger.info("ТЕСТ ЗАГРУЗКИ QWEN3-VL В РЕЖИМЕ TRANSFORMERS")
    logger.info("=" * 80)
    
    try:
        # Шаг 1: Загрузка модели
        logger.info("📥 Шаг 1: Загрузка модели Qwen3-VL...")
        model = ModelLoader.load_model("qwen3_vl_2b")
        logger.info("✅ Модель загружена успешно!")
        
        # Шаг 2: Создание тестового изображения
        logger.info("🖼️ Шаг 2: Создание тестового изображения...")
        test_image = create_test_image()
        logger.info("✅ Тестовое изображение создано")
        
        # Шаг 3: Обработка изображения
        logger.info("🔍 Шаг 3: Обработка изображения...")
        result = model.process_image(
            test_image,
            prompt="Describe this image.",
            max_new_tokens=50
        )
        logger.info(f"✅ Результат: {result}")
        
        # Шаг 4: Выгрузка модели
        logger.info("🗑️ Шаг 4: Выгрузка модели...")
        ModelLoader.unload_model("qwen3_vl_2b")
        logger.info("✅ Модель выгружена")
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("📝 Результаты:")
        logger.info("  ✅ Модель загружается без ошибок [Errno 22]")
        logger.info("  ✅ Обработка изображений работает")
        logger.info("  ✅ Выгрузка модели работает")
        logger.info("")
        logger.info("🎉 Режим Transformers полностью работоспособен!")
        
        return True
        
    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error("❌ ТЕСТ НЕ ПРОЙДЕН")
        logger.error("=" * 80)
        logger.error(f"Ошибка: {e}")
        
        import traceback
        logger.error("")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        
        return False

if __name__ == "__main__":
    success = test_qwen3_loading()
    sys.exit(0 if success else 1)
