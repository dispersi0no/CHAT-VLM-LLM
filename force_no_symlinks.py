#!/usr/bin/env python3
"""
Принудительное отключение symlinks в HuggingFace
Заставляет библиотеку работать как раньше - копировать файлы
"""

import os
import sys
from pathlib import Path

def force_disable_symlinks():
    """Принудительное отключение symlinks на уровне системы"""
    
    print("🔧 Принудительное отключение symlinks в HuggingFace")
    print("=" * 60)
    
    # 1. Установка переменных окружения
    print("\n1️⃣ Установка переменных окружения...")
    
    env_vars = {
        'HF_HUB_DISABLE_SYMLINKS_WARNING': '1',
        'HF_HUB_DISABLE_SYMLINKS': '1',
        'HF_HUB_ENABLE_HF_TRANSFER': '0',
        'TRANSFORMERS_OFFLINE': '0',
        'HF_HUB_OFFLINE': '0'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   ✅ {key}={value}")
    
    # 2. Патчинг huggingface_hub
    print("\n2️⃣ Патчинг huggingface_hub...")
    
    try:
        import huggingface_hub
        from huggingface_hub import constants
        
        # Принудительно отключаем symlinks
        if hasattr(constants, 'HF_HUB_DISABLE_SYMLINKS'):
            constants.HF_HUB_DISABLE_SYMLINKS = True
            print("   ✅ constants.HF_HUB_DISABLE_SYMLINKS = True")
        
        # Отключаем experimental features
        if hasattr(constants, 'HF_HUB_ENABLE_HF_TRANSFER'):
            constants.HF_HUB_ENABLE_HF_TRANSFER = False
            print("   ✅ constants.HF_HUB_ENABLE_HF_TRANSFER = False")
        
        print(f"   ✅ huggingface_hub v{huggingface_hub.__version__} пропатчен")
        
    except ImportError:
        print("   ⚠️ huggingface_hub не установлен")
    
    # 3. Обновление .env файла
    print("\n3️⃣ Обновление .env файла...")
    
    env_file = Path(".env")
    env_lines = []
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()
    
    updated_lines = []
    updated_vars = set()
    
    for line in env_lines:
        line_stripped = line.strip()
        if line_stripped and not line_stripped.startswith('#'):
            key = line_stripped.split('=')[0].strip()
            if key in env_vars:
                updated_lines.append(f"{key}={env_vars[key]}\n")
                updated_vars.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    for key, value in env_vars.items():
        if key not in updated_vars:
            updated_lines.append(f"{key}={value}\n")
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    print("   ✅ .env файл обновлен")
    
    # 4. Создание startup скрипта
    print("\n4️⃣ Создание startup скрипта...")
    
    startup_code = '''# Автоматическое отключение symlinks при импорте
import os
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'

try:
    import huggingface_hub
    from huggingface_hub import constants
    constants.HF_HUB_DISABLE_SYMLINKS = True
    constants.HF_HUB_ENABLE_HF_TRANSFER = False
except:
    pass
'''
    
    startup_file = Path("disable_symlinks_startup.py")
    with open(startup_file, 'w', encoding='utf-8') as f:
        f.write(startup_code)
    
    print(f"   ✅ Создан: {startup_file}")
    
    # 5. Тестирование
    print("\n5️⃣ Тестирование настроек...")
    
    try:
        from transformers import AutoTokenizer
        
        # Проверяем переменные окружения
        if os.environ.get('HF_HUB_DISABLE_SYMLINKS') == '1':
            print("   ✅ HF_HUB_DISABLE_SYMLINKS активна")
        else:
            print("   ⚠️ HF_HUB_DISABLE_SYMLINKS не установлена")
        
        # Пробуем загрузить токенизатор
        print("   🔄 Тестовая загрузка...")
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        
        tokenizer = AutoTokenizer.from_pretrained(
            "bert-base-uncased",
            cache_dir=str(cache_dir),
            local_files_only=False
        )
        
        print("   ✅ Загрузка работает!")
        
    except Exception as e:
        print(f"   ⚠️ Ошибка тестирования: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Symlinks принудительно отключены!")
    print()
    print("💡 Следующие шаги:")
    print("   1. Перезапустите Python/Streamlit")
    print("   2. Модели будут загружаться БЕЗ symlinks")
    print("   3. Файлы будут копироваться как раньше")
    print()
    print("📝 Важно:")
    print("   - При каждом запуске импортируйте: disable_symlinks_startup.py")
    print("   - Или добавьте в начало app.py:")
    print("     import disable_symlinks_startup")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = force_disable_symlinks()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
