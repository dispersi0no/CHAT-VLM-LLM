#!/usr/bin/env python3
"""
Исправление переключения моделей
Использует существующие контейнеры вместо создания новых
"""

import docker
import subprocess
import time
import requests

def check_container_exists(container_name):
    """Проверка существования контейнера"""
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        return True, container
    except docker.errors.NotFound:
        return False, None
    except Exception as e:
        return False, None

def stop_all_vllm_containers():
    """Остановка всех vLLM контейнеров"""
    client = docker.from_env()
    
    vllm_containers = [
        "dots-ocr-fixed",
        "qwen-qwen3-vl-2b-instruct-vllm",
        "qwen-qwen2-vl-2b-instruct-vllm",
        "microsoft-phi-3-5-vision-instruct-vllm"
    ]
    
    stopped = []
    
    for container_name in vllm_containers:
        try:
            container = client.containers.get(container_name)
            if container.status == "running":
                print(f"🛑 Остановка {container_name}...")
                container.stop(timeout=10)
                stopped.append(container_name)
        except docker.errors.NotFound:
            pass
        except Exception as e:
            print(f"⚠️ Ошибка остановки {container_name}: {e}")
    
    return stopped

def start_existing_container(container_name, port):
    """Запуск существующего контейнера"""
    try:
        client = docker.from_env()
        container = client.containers.get(container_name)
        
        if container.status == "running":
            print(f"✅ {container_name} уже запущен")
            return True
        
        print(f"🚀 Запуск {container_name}...")
        container.start()
        
        # Ожидание готовности API
        print(f"⏳ Ожидание готовности API на порту {port}...")
        
        max_wait = 120
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ API готов!")
                    return True
            except:
                pass
            
            elapsed = int(time.time() - start_time)
            print(f"   ⏳ {elapsed}с / {max_wait}с", end="\r")
            time.sleep(3)
        
        print(f"\n⚠️ Таймаут ожидания API")
        return False
        
    except docker.errors.NotFound:
        print(f"❌ Контейнер {container_name} не найден")
        print(f"   Необходимо создать контейнер или загрузить образ vllm/vllm-openai:latest")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def switch_model(model_key):
    """Переключение на указанную модель"""
    
    models_config = {
        "dots.ocr": {
            "container_name": "dots-ocr-fixed",
            "port": 8000,
            "display_name": "dots.ocr"
        },
        "qwen3-vl-2b": {
            "container_name": "qwen-qwen3-vl-2b-instruct-vllm",
            "port": 8004,
            "display_name": "Qwen3-VL 2B"
        },
        "qwen2-vl-2b": {
            "container_name": "qwen-qwen2-vl-2b-instruct-vllm",
            "port": 8001,
            "display_name": "Qwen2-VL 2B"
        },
        "phi35-vision": {
            "container_name": "microsoft-phi-3-5-vision-instruct-vllm",
            "port": 8002,
            "display_name": "Phi-3.5 Vision"
        }
    }
    
    if model_key not in models_config:
        print(f"❌ Неизвестная модель: {model_key}")
        return False
    
    config = models_config[model_key]
    
    print("=" * 60)
    print(f"🔄 Переключение на {config['display_name']}")
    print("=" * 60)
    print()
    
    # Шаг 1: Проверка существования контейнера
    print("1️⃣ Проверка контейнера...")
    exists, container = check_container_exists(config["container_name"])
    
    if not exists:
        print(f"❌ Контейнер {config['container_name']} не существует")
        print()
        print("💡 Решение:")
        print("   1. Загрузите образ: python pull_vllm_image.py")
        print("   2. Или создайте контейнер: python start_system.py")
        return False
    
    print(f"   ✅ Контейнер существует")
    
    # Шаг 2: Остановка других контейнеров
    print("\n2️⃣ Остановка других моделей...")
    stopped = stop_all_vllm_containers()
    
    if stopped:
        print(f"   ✅ Остановлено: {len(stopped)} контейнеров")
    else:
        print(f"   ℹ️ Нет активных контейнеров")
    
    time.sleep(2)
    
    # Шаг 3: Запуск целевого контейнера
    print(f"\n3️⃣ Запуск {config['display_name']}...")
    success = start_existing_container(config["container_name"], config["port"])
    
    if success:
        print()
        print("=" * 60)
        print(f"✅ Успешно переключено на {config['display_name']}")
        print("=" * 60)
        print()
        print(f"📡 API доступно: http://localhost:{config['port']}")
        print(f"📚 Документация: http://localhost:{config['port']}/docs")
        print()
        return True
    else:
        print()
        print("=" * 60)
        print(f"❌ Не удалось переключиться на {config['display_name']}")
        print("=" * 60)
        return False

def main():
    print("🎯 Исправление переключения моделей")
    print()
    print("Доступные модели:")
    print("  1. dots.ocr")
    print("  2. qwen3-vl-2b")
    print("  3. qwen2-vl-2b")
    print("  4. phi35-vision")
    print()
    print("Выберите модель (1-4) или введите ключ: ", end="")
    
    choice = input().strip()
    
    model_map = {
        "1": "dots.ocr",
        "2": "qwen3-vl-2b",
        "3": "qwen2-vl-2b",
        "4": "phi35-vision"
    }
    
    model_key = model_map.get(choice, choice)
    
    success = switch_model(model_key)
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
