#!/usr/bin/env python3
"""
Исправление кеша Qwen3-VL-2B-Instruct
Копирование файлов из blobs в snapshots
"""

import os
import shutil
from pathlib import Path

def fix_qwen3_cache():
    """Исправление кеша Qwen3-VL"""
    
    print("🔧 Исправление кеша Qwen3-VL-2B-Instruct")
    print("=" * 60)
    
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    model_dir = cache_dir / "models--Qwen--Qwen3-VL-2B-Instruct"
    
    if not model_dir.exists():
        print("❌ Модель не найдена в кеше")
        return False
    
    blobs_dir = model_dir / "blobs"
    snapshots_dir = model_dir / "snapshots"
    
    print(f"\n📂 Директория модели: {model_dir}")
    print(f"📦 Blobs: {blobs_dir}")
    print(f"📸 Snapshots: {snapshots_dir}")
    
    # Находим snapshot директорию
    snapshot_dirs = list(snapshots_dir.glob("*"))
    
    if not snapshot_dirs:
        print("\n❌ Snapshot директория не найдена")
        return False
    
    snapshot_dir = snapshot_dirs[0]
    print(f"\n🎯 Snapshot: {snapshot_dir.name}")
    
    # Список файлов для копирования
    files_to_copy = [
        "chat_template.json",
        "config.json",
        "generation_config.json",
        "merges.txt",
        "model.safetensors",
        "preprocessor_config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "vocab.json"
    ]
    
    print(f"\n🔄 Копирование файлов из blobs...")
    
    copied = 0
    failed = 0
    
    for filename in files_to_copy:
        target_file = snapshot_dir / filename
        
        # Проверяем, существует ли файл и доступен ли он
        try:
            if target_file.exists() and target_file.stat().st_size > 0:
                print(f"   ✅ {filename} (уже существует)")
                copied += 1
                continue
        except (OSError, PermissionError):
            # Файл недоступен - нужно скопировать
            pass
        
        # Ищем файл в blobs
        found = False
        for blob_file in blobs_dir.iterdir():
            if blob_file.is_file():
                try:
                    # Пробуем скопировать и проверить
                    temp_target = snapshot_dir / f"temp_{filename}"
                    shutil.copy2(blob_file, temp_target)
                    
                    # Проверяем размер
                    if temp_target.stat().st_size > 100:  # Минимальный размер
                        # Удаляем старый файл если есть
                        try:
                            if target_file.exists():
                                target_file.unlink()
                        except:
                            pass
                        
                        # Переименовываем
                        temp_target.rename(target_file)
                        print(f"   ✅ {filename} (скопирован из {blob_file.name[:16]}...)")
                        copied += 1
                        found = True
                        break
                    else:
                        temp_target.unlink()
                except Exception as e:
                    if temp_target.exists():
                        try:
                            temp_target.unlink()
                        except:
                            pass
                    continue
        
        if not found:
            print(f"   ⚠️ {filename} (не найден в blobs)")
            failed += 1
    
    print(f"\n" + "=" * 60)
    print(f"✅ Скопировано: {copied}")
    print(f"❌ Не найдено: {failed}")
    
    if failed > 0:
        print("\n⚠️ Некоторые файлы не найдены")
        print("💡 Попробуйте скачать модель заново")
        return False
    
    print("\n✅ Кеш исправлен!")
    return True

if __name__ == "__main__":
    import sys
    
    try:
        success = fix_qwen3_cache()
        
        if success:
            print("\n💡 Следующие шаги:")
            print("   1. Перезапустите систему: python start_system.py")
            print("   2. Попробуйте загрузить модель в Transformers режиме")
            print()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
