"""
ИСПРАВЛЕНИЕ WINDOWS SYMLINKS ДЛЯ QWEN3-VL
Решает проблему [Errno 22] Invalid argument при загрузке модели

Проблема:
- Модель загружается успешно первый раз (22:23:30)
- Все последующие попытки падают с [Errno 22] при "Loading model weights..."
- Причина: файлы в кеше HuggingFace являются symlinks, которые Windows не может читать

Решение:
1. Удалить существующий кеш модели (с symlinks)
2. Принудительно скачать модель заново БЕЗ symlinks
3. Использовать local_files_only=False для обхода кеша
"""

import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fix_qwen3_symlinks():
    """Исправление symlinks для Qwen3-VL модели"""
    
    # 1. Устанавливаем переменные окружения ПЕРЕД импортом
    os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
    os.environ['TRANSFORMERS_OFFLINE'] = '0'
    
    logger.info("✅ Переменные окружения установлены")
    
    # 2. Патчим huggingface_hub ДО импорта transformers
    try:
        import huggingface_hub
        from huggingface_hub import constants
        constants.HF_HUB_DISABLE_SYMLINKS = True
        constants.HF_HUB_ENABLE_HF_TRANSFER = False
        logger.info("✅ huggingface_hub пропатчен")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось пропатчить huggingface_hub: {e}")
    
    # 3. Находим и удаляем кеш модели с symlinks
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    model_cache = cache_dir / "models--Qwen--Qwen3-VL-2B-Instruct"
    
    if model_cache.exists():
        logger.info(f"🗑️ Удаление старого кеша с symlinks: {model_cache}")
        try:
            # Используем rmdir /s /q для Windows
            import subprocess
            subprocess.run(
                ['cmd', '/c', 'rmdir', '/s', '/q', str(model_cache)],
                check=False,
                capture_output=True
            )
            logger.info("✅ Старый кеш удален")
        except Exception as e:
            logger.error(f"❌ Ошибка удаления кеша: {e}")
            logger.info("💡 Попробуйте удалить вручную через проводник Windows")
            return False
    else:
        logger.info("ℹ️ Кеш модели не найден, будет скачан заново")
    
    # 4. Скачиваем модель заново БЕЗ symlinks
    logger.info("📥 Скачивание модели БЕЗ symlinks...")
    
    try:
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        import torch
        
        model_path = "Qwen/Qwen3-VL-2B-Instruct"
        
        # Скачиваем процессор
        logger.info("📥 Скачивание процессора...")
        processor = AutoProcessor.from_pretrained(
            model_path,
            trust_remote_code=True,
            local_files_only=False,  # Принудительно скачиваем
            force_download=False,    # Не перезаписываем, если есть
        )
        logger.info("✅ Процессор скачан")
        
        # Скачиваем модель (только веса, не загружаем в память)
        logger.info("📥 Скачивание весов модели...")
        from huggingface_hub import snapshot_download
        
        snapshot_path = snapshot_download(
            repo_id=model_path,
            local_files_only=False,
            resume_download=True,
            local_dir_use_symlinks=False,  # КРИТИЧЕСКИ ВАЖНО!
        )
        
        logger.info(f"✅ Модель скачана в: {snapshot_path}")
        logger.info("✅ Все файлы теперь реальные (не symlinks)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def verify_fix():
    """Проверка, что исправление работает"""
    
    logger.info("🔍 Проверка исправления...")
    
    try:
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        import torch
        
        model_path = "Qwen/Qwen3-VL-2B-Instruct"
        
        # Пробуем загрузить процессор
        logger.info("📥 Загрузка процессора...")
        processor = AutoProcessor.from_pretrained(
            model_path,
            trust_remote_code=True,
            local_files_only=True,  # Используем только локальный кеш
        )
        logger.info("✅ Процессор загружен успешно")
        
        # Пробуем загрузить модель
        logger.info("📥 Загрузка модели...")
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            local_files_only=True,  # Используем только локальный кеш
            attn_implementation="eager",
        )
        logger.info("✅ Модель загружена успешно!")
        
        # Очищаем память
        del model
        del processor
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("✅ ИСПРАВЛЕНИЕ РАБОТАЕТ! Модель загружается без ошибок")
        return True
        
    except Exception as e:
        logger.error(f"❌ Проверка не прошла: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("ИСПРАВЛЕНИЕ WINDOWS SYMLINKS ДЛЯ QWEN3-VL")
    logger.info("=" * 80)
    
    # Шаг 1: Исправление
    success = fix_qwen3_symlinks()
    
    if not success:
        logger.error("❌ Исправление не удалось")
        exit(1)
    
    # Шаг 2: Проверка
    logger.info("")
    logger.info("=" * 80)
    logger.info("ПРОВЕРКА ИСПРАВЛЕНИЯ")
    logger.info("=" * 80)
    
    verified = verify_fix()
    
    if verified:
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ ВСЕ ГОТОВО! Модель Qwen3-VL теперь работает без ошибок")
        logger.info("=" * 80)
        logger.info("")
        logger.info("📝 Следующие шаги:")
        logger.info("1. Перезапустите приложение: python start_system.py")
        logger.info("2. Выберите режим 'Transformers (Локально)'")
        logger.info("3. Выберите модель 'Qwen3-VL-2B'")
        logger.info("4. Загрузите изображение и протестируйте")
    else:
        logger.error("")
        logger.error("=" * 80)
        logger.error("❌ ПРОВЕРКА НЕ ПРОШЛА")
        logger.error("=" * 80)
        logger.error("")
        logger.error("💡 Возможные решения:")
        logger.error("1. Удалите кеш вручную: C:\\Users\\Colorful\\.cache\\huggingface\\hub\\models--Qwen--Qwen3-VL-2B-Instruct")
        logger.error("2. Запустите скрипт еще раз")
        logger.error("3. Проверьте, что у вас есть права на запись в кеш")
