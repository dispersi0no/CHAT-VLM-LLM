"""
Запуск системы с ПРИНУДИТЕЛЬНОЙ установкой переменных окружения
"""

import os
import sys
import subprocess

# КРИТИЧЕСКИ ВАЖНО: Устанавливаем переменные окружения ПЕРЕД любыми импортами
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
os.environ['TRANSFORMERS_OFFLINE'] = '0'
os.environ['HF_HUB_OFFLINE'] = '0'
os.environ['HF_HOME'] = r'C:\Users\Colorful\.cache\huggingface'
os.environ['TRANSFORMERS_CACHE'] = r'C:\Users\Colorful\.cache\huggingface\hub'

print("=" * 80)
print("🔧 УСТАНОВКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
print("=" * 80)
print(f"✅ HF_HUB_DISABLE_SYMLINKS = {os.environ['HF_HUB_DISABLE_SYMLINKS']}")
print(f"✅ HF_HUB_ENABLE_HF_TRANSFER = {os.environ['HF_HUB_ENABLE_HF_TRANSFER']}")
print(f"✅ HF_HOME = {os.environ['HF_HOME']}")
print(f"✅ TRANSFORMERS_CACHE = {os.environ['TRANSFORMERS_CACHE']}")
print("=" * 80)
print()

# Запускаем start_system.py с этими переменными
print("🚀 Запуск start_system.py...")
subprocess.run([sys.executable, "start_system.py"], env=os.environ.copy())
