#!/usr/bin/env python3
"""
Исправление проблемы [Errno 22] Invalid argument на Windows
Проблема: HuggingFace создает пути с недопустимыми символами для Windows
"""

import os
import sys
from pathlib import Path

def fix_windows_cache():
    """Исправление путей кеша для Windows"""
    
    print("🔧 Исправление путей кеша HuggingFace для Windows")
    print("=" * 60)
    
    # 1. Установка переменных окружения для корректных путей
    print("\n1️⃣ Настройка переменных окружения...")
    
    # Используем короткий путь без специальных символов
    cache_dir = Path.home() / ".cache" / "huggingface"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Устанавливаем переменные окружения
    os.environ['HF_HOME'] = str(cache_dir)
    os.environ['TRANSFORMERS_CACHE'] = str(cache_dir / "hub")
    os.environ['HF_DATASETS_CACHE'] = str(cache_dir / "datasets")
    os.environ['HUGGINGFACE_HUB_CACHE'] = str(cache_dir / "hub")
    
    print(f"   ✅ HF_HOME: {cache_dir}")
    print(f"   ✅ TRANSFORMERS_CACHE: {cache_dir / 'hub'}")
    
    # 2. Отключение проблемных функций
    print("\n2️⃣ Отключение проблемных функций...")
    
    # Отключаем symlinks (проблема на Windows)
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
    
    # Отключаем telemetry
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    
    # Отключаем прогресс бары (могут вызывать проблемы)
    os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '0'
    
    print("   ✅ Symlinks отключены")
    print("   ✅ Telemetry отключена")
    
    # 3. Исправление путей в существующем кеше
    print("\n3️⃣ Проверка существующего кеша...")
    
    hub_cache = cache_dir / "hub"
    if hub_cache.exists():
        print(f"   ✅ Кеш найден: {hub_cache}")
        
        # Подсчет моделей в кеше
        model_dirs = list(hub_cache.glob("models--*"))
        print(f"   📦 Моделей в кеше: {len(model_dirs)}")
        
        # Проверка проблемных путей
        problematic_paths = []
        for model_dir in model_dirs:
            for file_path in model_dir.rglob("*"):
                if any(char in str(file_path) for char in [':', '*', '?', '"', '<', '>', '|']):
                    problematic_paths.append(file_path)
        
        if problematic_paths:
            print(f"   ⚠️ Найдено проблемных путей: {len(problematic_paths)}")
            print("   💡 Рекомендуется очистить кеш: python clear_cache.py")
        else:
            print("   ✅ Проблемных путей не найдено")
    else:
        print("   ℹ️ Кеш пуст (будет создан при загрузке)")
    
    # 4. Создание .env файла с настройками
    print("\n4️⃣ Обновление .env файла...")
    
    env_file = Path(".env")
    env_lines = []
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()
    
    # Обновляем или добавляем переменные
    env_vars = {
        'HF_HOME': str(cache_dir),
        'TRANSFORMERS_CACHE': str(cache_dir / 'hub'),
        'HF_HUB_DISABLE_SYMLINKS': '1',
        'HF_HUB_DISABLE_SYMLINKS_WARNING': '1',
        'HF_HUB_DISABLE_TELEMETRY': '1'
    }
    
    updated_lines = []
    updated_vars = set()
    
    for line in env_lines:
        line = line.strip()
        if line and not line.startswith('#'):
            key = line.split('=')[0].strip()
            if key in env_vars:
                updated_lines.append(f"{key}={env_vars[key]}\n")
                updated_vars.add(key)
            else:
                updated_lines.append(line + '\n')
        else:
            updated_lines.append(line + '\n')
    
    # Добавляем новые переменные
    for key, value in env_vars.items():
        if key not in updated_vars:
            updated_lines.append(f"{key}={value}\n")
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    print(f"   ✅ .env файл обновлен")
    
    # 5. Тестирование
    print("\n5️⃣ Тестирование настроек...")
    
    try:
        from transformers import AutoTokenizer
        
        # Пробуем загрузить простой токенизатор
        print("   🔄 Тестовая загрузка токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(
            "bert-base-uncased",
            cache_dir=str(cache_dir / "hub")
        )
        print("   ✅ Тестовая загрузка успешна!")
        
    except Exception as e:
        print(f"   ⚠️ Ошибка тестирования: {e}")
        print("   💡 Попробуйте перезапустить Python")
    
    print("\n" + "=" * 60)
    print("✅ Исправление завершено!")
    print()
    print("💡 Следующие шаги:")
    print("   1. Перезапустите Python/Streamlit")
    print("   2. Попробуйте загрузить модель снова")
    print("   3. Если проблема сохраняется:")
    print("      - Очистите кеш: python clear_cache.py")
    print("      - Перезагрузите компьютер")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = fix_windows_cache()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
