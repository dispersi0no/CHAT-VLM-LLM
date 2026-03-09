#!/usr/bin/env python3
"""
Остановка системы ChatVLMLLM
Корректное завершение всех компонентов
"""

import logging
import subprocess
import time

from utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


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
    logger.info("Остановка системы ChatVLMLLM")

    # 1. Остановка Streamlit
    logger.info("1. Остановка Streamlit...")
    success, stdout, stderr = run_command("taskkill /F /IM streamlit.exe")
    if success or "не найден" in stderr:
        logger.info("Streamlit остановлен")
    else:
        logger.warning("%s", stderr)

    # 2. Остановка контейнеров
    logger.info("2. Остановка контейнеров...")

    containers = [
        "dots-ocr-fixed",
        "dots-ocr-stable",
        "dots-ocr-optimized",
        "dots-ocr-performance",
    ]

    for container in containers:
        success, stdout, stderr = run_command(f"docker stop {container}")
        if success:
            logger.info("Остановлен: %s", container)
            # Удаляем контейнер
            run_command(f"docker rm {container}")
        elif "No such container" not in stderr:
            logger.warning("%s: %s", container, stderr)

    # 3. Проверка GPU
    logger.info("3. Проверка освобождения GPU...")
    time.sleep(3)

    success, stdout, stderr = run_command(
        "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits"
    )
    if success and stdout.strip():
        memory_used = int(stdout.strip())
        if memory_used < 1000:  # Меньше 1GB
            logger.info("GPU освобожден: %sMB используется", memory_used)
        else:
            logger.warning("GPU память: %sMB (может потребоваться время)", memory_used)

    # 4. Очистка процессов Python (если нужно)
    logger.info("4. Очистка процессов...")

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
            logger.warning("Найдены процессы Python со Streamlit")
            logger.warning("Рекомендуется завершить их вручную если нужно")
        else:
            logger.info("Процессы Python очищены")

    logger.info("СИСТЕМА ОСТАНОВЛЕНА")
    logger.info("Для повторного запуска используйте: python start_system.py")


if __name__ == "__main__":
    main()
