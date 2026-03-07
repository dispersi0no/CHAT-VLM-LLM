"""
Мониторинг логов системы в реальном времени
"""

import time
import subprocess
import sys
from datetime import datetime

def print_header(text):
    """Печать заголовка"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")

def monitor_streamlit_logs():
    """Мониторинг логов Streamlit"""
    print_header("📊 МОНИТОРИНГ ЛОГОВ STREAMLIT")
    
    log_file = "logs/chatvlmllm_20260304.log"
    
    try:
        # Показываем последние 50 строк
        result = subprocess.run(
            ["powershell", "-Command", f"Get-Content {log_file} -Tail 50"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Ошибка чтения логов: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def monitor_docker_logs():
    """Мониторинг логов Docker контейнера"""
    print_header("🐳 МОНИТОРИНГ ЛОГОВ DOCKER (dots.ocr)")
    
    try:
        result = subprocess.run(
            ["docker", "logs", "dots-ocr-fixed", "--tail", "30"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
        else:
            print(f"❌ Контейнер не найден или не запущен")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def check_system_status():
    """Проверка статуса системы"""
    print_header("🔍 СТАТУС СИСТЕМЫ")
    
    # Проверка Streamlit
    try:
        result = subprocess.run(
            ["powershell", "-Command", "curl http://localhost:8501 -UseBasicParsing | Select-Object -ExpandProperty StatusCode"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "200" in result.stdout:
            print("✅ Streamlit UI: РАБОТАЕТ (http://localhost:8501)")
        else:
            print("❌ Streamlit UI: НЕ ОТВЕЧАЕТ")
    except:
        print("❌ Streamlit UI: НЕ ОТВЕЧАЕТ")
    
    # Проверка vLLM API
    try:
        result = subprocess.run(
            ["powershell", "-Command", "curl http://localhost:8000/v1/models -UseBasicParsing | Select-Object -ExpandProperty StatusCode"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "200" in result.stdout:
            print("✅ vLLM API: РАБОТАЕТ (http://localhost:8000)")
        else:
            print("❌ vLLM API: НЕ ОТВЕЧАЕТ")
    except:
        print("❌ vLLM API: НЕ ОТВЕЧАЕТ")
    
    # Проверка Docker контейнера
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=dots-ocr-fixed", "--format", "{{.Status}}"],
            capture_output=True,
            text=True
        )
        
        if "Up" in result.stdout:
            print(f"✅ Docker контейнер: РАБОТАЕТ ({result.stdout.strip()})")
        else:
            print("❌ Docker контейнер: НЕ ЗАПУЩЕН")
    except:
        print("❌ Docker: НЕ ДОСТУПЕН")
    
    # GPU статус
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            used, total = result.stdout.strip().split(',')
            print(f"✅ GPU: {used.strip()} MB / {total.strip()} MB используется")
        else:
            print("⚠️ GPU: Информация недоступна")
    except:
        print("⚠️ GPU: nvidia-smi не найден")

def main():
    """Главная функция"""
    print("\n" + "🔍" * 40)
    print(f"  МОНИТОРИНГ СИСТЕМЫ CHATVLMLLM")
    print(f"  Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔍" * 40)
    
    # Статус системы
    check_system_status()
    
    # Логи Streamlit
    monitor_streamlit_logs()
    
    # Логи Docker
    monitor_docker_logs()
    
    print("\n" + "=" * 80)
    print("💡 Для непрерывного мониторинга используйте:")
    print("   Streamlit: tail -f logs/chatvlmllm_20260304.log")
    print("   Docker:    docker logs -f dots-ocr-fixed")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Мониторинг остановлен")
        sys.exit(0)
