#!/usr/bin/env python3
"""
Окончательное решение проблемы symlinks на Windows
Конвертирует symlinks в реальные файлы
"""

import os
import shutil
from pathlib import Path
import sys

def fix_symlinks_in_cache():
    """Исправление symlinks в кеше HuggingFace"""
    
    print("🔧 Исправление symlinks в кеше HuggingFace")
    print("=" * 60)
    
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    
    if not cache_dir.exists():
        print("❌ Кеш не найден")
        return False
    
    print(f"\n📂 Директория кеша: {cache_dir}")
    
    # Находим все symlinks
    symlinks_found = []
    symlinks_fixed = []
    symlinks_failed = []
    
    print("\n🔍 Поиск symlinks...")
    
    for root, dirs, files in os.walk(cache_dir):
        root_path = Path(root)
        
        # Проверяем файлы
        for file in files:
            file_path = root_path / file
            try:
                if file_path.is_symlink():
                    symlinks_found.append(file_path)
            except (OSError, PermissionError):
                # Файл недоступен - вероятно symlink
                symlinks_found.append(file_path)
    
    print(f"   Найдено symlinks: {len(symlinks_found)}")
    
    if not symlinks_found:
        print("   ✅ Symlinks не найдены")
        return True
    
    print(f"\n🔄 Конвертация {len(symlinks_found)} symlinks в реальные файлы...")
    
    for symlink_path in symlinks_found:
        try:
            # Пытаемся прочитать целевой файл
            if symlink_path.is_symlink():
                target = symlink_path.resolve()
                
                if target.exists():
                    # Удаляем symlink
                    symlink_path.unlink()
                    
                    # Копируем реальный файл
                    shutil.copy2(target, symlink_path)
                    
                    symlinks_fixed.append(str(symlink_path))
                    print(f"   ✅ {symlink_path.name}")
                else:
                    symlinks_failed.append(str(symlink_path))
                    print(f"   ⚠️ {symlink_path.name} (цель не найдена)")
            else:
                # Файл недоступен - удаляем
                try:
                    symlink_path.unlink()
                    symlinks_fixed.append(str(symlink_path))
                    print(f"   ✅ {symlink_path.name} (удален)")
                except:
                    symlinks_failed.append(str(symlink_path))
                    print(f"   ❌ {symlink_path.name} (не удалось удалить)")
                    
        except Exception as e:
            symlinks_failed.append(str(symlink_path))
            print(f"   ❌ {symlink_path.name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Исправлено: {len(symlinks_fixed)}")
    print(f"❌ Ошибок: {len(symlinks_failed)}")
    
    if symlinks_failed:
        print("\n⚠️ Не удалось исправить некоторые файлы")
        print("💡 Рекомендуется полная очистка кеша")
        return False
    
    return True

def main():
    print("🎯 Окончательное решение проблемы symlinks")
    print()
    
    # Устанавливаем переменные окружения
    cache_dir = Path.home() / ".cache" / "huggingface"
    os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
    os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
    
    print("1️⃣ Отключение symlinks в переменных окружения...")
    print("   ✅ HF_HUB_DISABLE_SYMLINKS=1")
    
    print("\n2️⃣ Исправление существующих symlinks...")
    success = fix_symlinks_in_cache()
    
    if not success:
        print("\n❌ Не удалось исправить все symlinks")
        print("\n💡 Рекомендуется:")
        print("   1. Полная очистка кеша: python clear_cache.py")
        print("   2. Или используйте vLLM режим (без проблем с symlinks)")
        return False
    
    print("\n3️⃣ Обновление .env файла...")
    
    env_file = Path(".env")
    env_lines = []
    
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_lines = f.readlines()
    
    # Добавляем/обновляем переменные
    env_vars = {
        'HF_HUB_DISABLE_SYMLINKS': '1',
        'HF_HUB_DISABLE_SYMLINKS_WARNING': '1',
        'HF_HUB_ENABLE_HF_TRANSFER': '0'
    }
    
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
    
    print("\n" + "=" * 60)
    print("✅ Исправление завершено!")
    print()
    print("💡 Следующие шаги:")
    print("   1. Перезапустите систему: python start_system.py")
    print("   2. Модели будут загружаться БЕЗ symlinks")
    print("   3. Проблема больше не повторится")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
