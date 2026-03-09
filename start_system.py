#!/usr/bin/env python3
"""
Быстрый запуск системы ChatVLMLLM
Единообразный запуск на стандартных портах
"""

import logging
import os
import subprocess
import sys
import time

import requests

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
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def check_port(port, timeout=5):
    """Проверка доступности порта"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=timeout)
        return response.status_code == 200
    except:
        return False


def main():
    logger.info("Запуск системы ChatVLMLLM")

    # 1. Проверяем и останавливаем существующие процессы
    logger.info("1. Очистка существующих процессов...")

    # Останавливаем Streamlit
    success, stdout, stderr = run_command("taskkill /F /IM streamlit.exe 2>nul")
    if success:
        logger.info("Streamlit процессы остановлены")

    # Останавливаем и удаляем ВСЕ старые контейнеры vLLM
    old_containers = [
        "dots-ocr-stable",
        "dots-ocr-optimized",
        "dots-ocr-performance",
        "dots-ocr-fixed",
        "qwen-qwen3-vl-2b-instruct-vllm",
        "qwen-qwen2-vl-2b-instruct-vllm",
        "microsoft-phi-3-5-vision-instruct-vllm",
    ]

    for container in old_containers:
        run_command(f"docker stop {container} 2>nul")
        run_command(f"docker rm {container} 2>nul")

    logger.info("Старые контейнеры очищены")

    # 2. Запускаем dots.ocr контейнер
    logger.info("2. Запуск dots.ocr модели...")

    # Проверяем, не запущен ли уже правильный контейнер
    success, stdout, stderr = run_command(
        "docker ps --filter name=dots-ocr-fixed --format '{{.Names}}'"
    )
    if "dots-ocr-fixed" in stdout:
        logger.info("Контейнер dots-ocr-fixed уже запущен")
    else:
        # Останавливаем и удаляем если есть
        run_command("docker stop dots-ocr-fixed 2>nul")
        run_command("docker rm dots-ocr-fixed 2>nul")

        # Запускаем новый контейнер
        docker_cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            "dots-ocr-fixed",
            "--gpus",
            "all",
            "-p",
            "8000:8000",
            "--shm-size=8g",
            "-v",
            f"{os.path.expanduser('~/.cache/huggingface')}:/root/.cache/huggingface:rw",
            "-e",
            "CUDA_VISIBLE_DEVICES=0",
            "-e",
            "HF_HOME=/root/.cache/huggingface",
            "-e",
            "TRANSFORMERS_CACHE=/root/.cache/huggingface/hub",
            "vllm/vllm-openai:latest",
            "--model",
            "rednote-hilab/dots.ocr",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--trust-remote-code",
            "--max-model-len",
            "4096",
            "--gpu-memory-utilization",
            "0.85",
            "--dtype",
            "bfloat16",
            "--enforce-eager",
            "--disable-log-requests",
        ]

        success, stdout, stderr = run_command(docker_cmd, shell=False)
        if success:
            logger.info("Контейнер dots-ocr-fixed запущен")
        else:
            logger.error("Ошибка запуска контейнера: %s", stderr)
            return False

    # 3. Ожидание готовности API
    logger.info("3. Ожидание готовности модели...")

    max_wait = 180  # 3 минуты (увеличено с 2 минут)
    start_time = time.time()

    while time.time() - start_time < max_wait:
        if check_port(8000):
            logger.info("API dots.ocr готов!")
            break

        elapsed = int(time.time() - start_time)
        logger.info("Загрузка модели... (%ss/%ss)", elapsed, max_wait)
        time.sleep(5)
    else:
        logger.error("Таймаут загрузки модели")
        return False

    # 4. Запуск Streamlit приложения
    logger.info("4. Запуск Streamlit приложения...")

    # Очищаем кеши
    cache_dirs = [os.path.expanduser("~/.streamlit"), "__pycache__"]

    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                if os.path.isdir(cache_dir):
                    import shutil

                    shutil.rmtree(cache_dir)
                else:
                    os.remove(cache_dir)
                logger.info("Очищен кеш: %s", cache_dir)
            except (OSError, PermissionError) as exc:
                logger.warning("Не удалось очистить кеш %s: %s", cache_dir, exc)

    # Запускаем Streamlit
    logger.info("Запуск Streamlit на http://localhost:8501...")

    try:
        # Запускаем в фоновом режиме
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.port",
                "8501",
                "--server.headless",
                "true",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Ждем запуска
        time.sleep(10)

        # Проверяем доступность
        try:
            response = requests.get("http://localhost:8501", timeout=5)
            if response.status_code == 200:
                logger.info("Streamlit запущен успешно!")
            else:
                logger.warning("Streamlit отвечает с кодом: %s", response.status_code)
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Streamlit запускается... (может потребоваться время): %s", exc
            )

    except Exception as e:
        logger.error("Ошибка запуска Streamlit: %s", e)
        return False

    # 5. Финальная проверка
    logger.info("5. Финальная проверка системы...")

    # Проверяем GPU
    success, stdout, stderr = run_command(
        "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits"
    )
    if success and stdout.strip():
        memory_used = int(stdout.strip())
        if memory_used > 5000:  # Больше 5GB
            logger.info("GPU активен: %sMB используется", memory_used)
        else:
            logger.warning(
                "GPU память: %sMB (модель может еще загружаться)", memory_used
            )

    # Проверяем контейнер
    success, stdout, stderr = run_command(
        "docker ps --filter name=dots-ocr-fixed --format '{{.Status}}'"
    )
    if "Up" in stdout:
        logger.info("Контейнер dots-ocr-fixed работает")
    else:
        logger.error("Проблема с контейнером")

    logger.info("СИСТЕМА ЗАПУЩЕНА!")
    logger.info("Streamlit: http://localhost:8501")
    logger.info("dots.ocr API: http://localhost:8000")

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Ошибка запуска системы")
        sys.exit(1)
    else:
        logger.info("Система готова к работе!")
        sys.exit(0)
