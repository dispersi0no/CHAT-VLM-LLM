#!/usr/bin/env python3
"""
Скрипт для загрузки vLLM Docker образа
"""

import subprocess
import sys
import time

def run_command(cmd, shell=True):
    """Выполнение команды с выводом"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 60)
    print("🐳 Загрузка vLLM Docker образа")
    print("=" * 60)
    print()
    
    # Проверка Docker
    print("1️⃣ Проверка Docker...")
    success, stdout, stderr = run_command("docker --version")
    
    if not success:
        print("❌ Docker не найден или не запущен")
        print("   Убедитесь, что Docker Desktop запущен")
        return False
    
    print(f"   ✅ {stdout.strip()}")
    
    # Проверка существующего образа
    print("\n2️⃣ Проверка существующего образа...")
    success, stdout, stderr = run_command("docker images vllm/vllm-openai:latest --format '{{.Repository}}:{{.Tag}}'")
    
    if success and "vllm/vllm-openai:latest" in stdout:
        print("   ✅ Образ vllm/vllm-openai:latest уже существует")
        print("\n   Хотите обновить до последней версии? (y/n): ", end="")
        
        choice = input().lower()
        if choice != 'y':
            print("   ℹ️ Пропуск загрузки")
            return True
    else:
        print("   ℹ️ Образ не найден, начинаем загрузку...")
    
    # Загрузка образа
    print("\n3️⃣ Загрузка образа vllm/vllm-openai:latest...")
    print("   ⏳ Это может занять 5-10 минут (~8-10 GB)")
    print("   📊 Прогресс загрузки:")
    print()
    
    start_time = time.time()
    
    # Запускаем docker pull с выводом в реальном времени
    process = subprocess.Popen(
        ["docker", "pull", "vllm/vllm-openai:latest"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Читаем вывод построчно
    for line in process.stdout:
        print(f"   {line.strip()}")
    
    process.wait()
    
    elapsed_time = time.time() - start_time
    
    if process.returncode == 0:
        print()
        print("=" * 60)
        print("✅ Образ успешно загружен!")
        print("=" * 60)
        print(f"⏱️ Время загрузки: {int(elapsed_time)} секунд")
        print()
        
        # Проверка размера образа
        print("📊 Информация об образе:")
        success, stdout, stderr = run_command("docker images vllm/vllm-openai:latest")
        if success:
            print(stdout)
        
        print()
        print("🎉 Теперь переключение моделей будет работать!")
        print()
        print("💡 Следующие шаги:")
        print("   1. Запустите: python start_system.py")
        print("   2. Откройте Streamlit: http://localhost:8501")
        print("   3. Используйте кнопку переключения моделей")
        
        return True
    else:
        print()
        print("=" * 60)
        print("❌ Ошибка загрузки образа")
        print("=" * 60)
        print()
        print("🔍 Возможные причины:")
        print("   1. Нет подключения к интернету")
        print("   2. Docker Hub недоступен")
        print("   3. Недостаточно места на диске (~10 GB)")
        print("   4. Docker Desktop не запущен")
        print()
        print("🛠️ Попробуйте:")
        print("   - Проверить подключение к интернету")
        print("   - Перезапустить Docker Desktop")
        print("   - Освободить место на диске")
        print("   - Запустить вручную: docker pull vllm/vllm-openai:latest")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
