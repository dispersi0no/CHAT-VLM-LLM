@echo off
echo ========================================
echo Загрузка vLLM Docker образа
echo ========================================
echo.

echo Это может занять 5-10 минут в зависимости от скорости интернета...
echo Размер образа: ~8-10 GB
echo.

echo Загрузка vllm/vllm-openai:latest...
docker pull vllm/vllm-openai:latest

if %errorlevel% == 0 (
    echo.
    echo ========================================
    echo ✅ Образ успешно загружен!
    echo ========================================
    echo.
    echo Теперь переключение моделей будет работать.
    echo.
    echo Проверка образа:
    docker images vllm/vllm-openai
) else (
    echo.
    echo ========================================
    echo ❌ Ошибка загрузки образа
    echo ========================================
    echo.
    echo Проверьте:
    echo 1. Подключение к интернету
    echo 2. Docker Desktop запущен
    echo 3. Достаточно места на диске (~10 GB)
)

echo.
pause
