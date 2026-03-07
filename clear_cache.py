#!/usr/bin/env python3
"""
Очистка кеша HuggingFace для решения проблем с путями
"""

import shutil
from pathlib import Path
import sys

def clear_huggingface_cache():
    """Очистка кеша HuggingFace"""
    
    print("🧹 Очистка кеша HuggingFace")
    print("=" * 60)
    
    cache_dir = Path.home() / ".cache" / "huggingface"
    
    if not cache_dir.exists():
        print("ℹ️ Кеш не найден (уже пуст)")
        return True
    
    print(f"\n📂 Директория кеша: {cache_dir}")
    
    # Подсчет размера (с обработкой ошибок symlinks)
    total_size = 0
    file_count = 0
    
    try:
        for file_path in cache_dir.rglob("*"):
            try:
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            except (OSError, PermissionError):
                # Пропускаем проблемные файлы (symlinks, недоступные файлы)
                pass
    except Exception:
        pass
    
    size_gb = total_size / (1024 ** 3) if total_size > 0 else 0
    
    if file_count > 0:
        print(f"📊 Размер кеша: {size_gb:.2f} GB ({file_count} файлов)")
    else:
        print(f"📊 Размер кеша: Невозможно подсчитать (проблемы с symlinks)")
    print()
    print("⚠️ ВНИМАНИЕ: Это удалит все загруженные модели!")
    print("   Модели придется загрузить заново при следующем использовании.")
    print()
    
    response = input("Продолжить очистку? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y', 'да']:
        print("❌ Очистка отменена")
        return False
    
    print("\n🗑️ Удаление кеша...")
    
    try:
        shutil.rmtree(cache_dir)
        print("✅ Кеш успешно удален")
        
        # Пересоздаем директорию
        cache_dir.mkdir(parents=True, exist_ok=True)
        print("✅ Директория кеша пересоздана")
        
        print()
        print("=" * 60)
        print("✅ Очистка завершена!")
        print()
        print("💡 Следующие шаги:")
        print("   1. Запустите: python fix_windows_cache_paths.py")
        print("   2. Перезапустите приложение")
        print("   3. Модели загрузятся заново")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        print()
        print("💡 Попробуйте:")
        print("   1. Закрыть все Python процессы")
        print("   2. Удалить вручную: " + str(cache_dir))
        print("   3. Перезагрузить компьютер")
        return False

if __name__ == "__main__":
    try:
        success = clear_huggingface_cache()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
