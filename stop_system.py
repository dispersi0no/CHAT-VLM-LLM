#!/usr/bin/env python3
"""
Остановка системы ChatVLMLLM
Корректное завершение всех компонентов
"""

import subprocess
import time


def run_command(cmd, shell=True):
    """Выполнение команды с выводом"""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def main():
    print("🛑 Остановка системы ChatVLMLLM")
    print("=" * 40)

    # 1. Остановка Streamlit
    print("1️⃣ Остановка Streamlit...")
    success, stdout, stderr = run_command("taskkill /F /IM streamlit.exe")
    if success or "не найден" in stderr:
        print("   ✅ Streamlit остановлен")
    else:
        print(f"   ⚠️ {stderr}")

    # 2. Остановка контейнеров
    print("\n2️⃣ Остановка контейнеров...")

    containers = [
        "dots-ocr-fixed",
        "dots-ocr-stable",
        "dots-ocr-optimized",
        "dots-ocr-performance",
    ]

    for container in containers:
        success, stdout, stderr = run_command(f"docker stop {container}")
        if success:
            print(f"   ✅ Остановлен: {container}")
            # Удаляем контейнер
            run_command(f"docker rm {container}")
        elif "No such container" not in stderr:
            print(f"   ⚠️ {container}: {stderr}")

    # 3. Проверка GPU
    print("\n3️⃣ Проверка освобождения GPU...")
    time.sleep(3)

    success, stdout, stderr = run_command(
        "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits"
    )
    if success and stdout.strip():
        memory_used = int(stdout.strip())
        if memory_used < 1000:  # Меньше 1GB
            print(f"   ✅ GPU освобожден: {memory_used}MB используется")
        else:
            print(f"   ⚠️ GPU память: {memory_used}MB (может потребоваться время)")

    # 4. Очистка процессов Python (если нужно)
    print("\n4️⃣ Очистка процессов...")

    success, stdout, stderr = run_command(
        'tasklist /FI "IMAGENAME eq python.exe" /FO CSV'
    )
    if success and "python.exe" in stdout:
        lines = stdout.split("\n")
        python_processes = [
            line
            for line in lines
            if "python.exe" in line and "streamlit" in line.lower()
        ]

        if python_processes:
            print("   ⚠️ Найдены процессы Python со Streamlit")
            print("   💡 Рекомендуется завершить их вручную если нужно")
        else:
            print("   ✅ Процессы Python очищены")

    print("\n" + "=" * 40)
    print("✅ СИСТЕМА ОСТАНОВЛЕНА")
    print()
    print("💡 Для повторного запуска используйте:")
    print("   python start_system.py")


if __name__ == "__main__":
    main()
