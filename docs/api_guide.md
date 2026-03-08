# Руководство по REST API

## Обзор

ChatVLMLLM предоставляет REST API на базе FastAPI для программного доступа к функциям OCR и визуального понимания.

## Запуск сервера

```bash
# Режим разработки с автоперезагрузкой
uvicorn api:app --host 0.0.0.0 --port 8001 --reload --workers 1

# Продакшен режим
uvicorn api:app --host 0.0.0.0 --port 8001 --workers 1
```

> **ВАЖНО:** Запускайте с `--workers 1`. Несколько воркеров вызовут конфликт кешей моделей в GPU памяти.

## Документация API

После запуска сервера доступна интерактивная документация:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

## Эндпоинты

### Системные

#### GET /
Корневой эндпоинт с информацией об API.

```bash
curl http://localhost:8001/
```

Ответ:
```json
{
  "message": "ChatVLMLLM API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

#### GET /health
Проверка здоровья сервиса и статуса GPU.

```bash
curl http://localhost:8001/health
```

Ответ:
```json
{
  "status": "healthy",
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 4090",
  "models_loaded": 1,
  "loaded_models": ["qwen3_vl_2b"]
}
```

#### GET /models
Список доступных моделей.

```bash
curl http://localhost:8001/models
```

Ответ:
```json
{
  "available": [
    {"id": "qwen3_vl_2b", "name": "Qwen3-VL 2B", "params": "2B", "status": "working"},
    {"id": "qwen_vl_2b", "name": "Qwen2-VL 2B", "params": "2B", "status": "unstable"},
    {"id": "dots_ocr", "name": "dots.ocr", "params": "1.7B", "status": "working"},
    {"id": "dots_ocr_final", "name": "dots.ocr Final", "params": "1.7B", "status": "working"},
    {"id": "got_ocr", "name": "GOT-OCR 2.0", "params": "580M", "status": "experimental"}
  ],
  "loaded": ["qwen3_vl_2b"]
}
```

> **Примечание:** Основные модели — Qwen3-VL 2B и dots.ocr. Qwen2-VL 7B и Phi-3.5 Vision доступны только через vLLM режим (docker-compose-vllm.yml), а не через этот API.

### OCR

#### POST /ocr
Извлечение текста из изображения.

**Параметры:**
| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| file | File | Да | Изображение (JPG, PNG, BMP, TIFF, WebP) |
| model | string | Нет | Модель (по умолчанию: qwen3_vl_2b) |
| language | string | Нет | Подсказка языка |

**Пример с cURL:**
```bash
curl -X POST "http://localhost:8001/ocr" \
  -F "file=@document.jpg" \
  -F "model=qwen3_vl_2b"
```

**Пример с Python:**
```python
import requests

with open('document.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8001/ocr',
        files={'file': f},
        params={'model': 'qwen3_vl_2b', 'language': 'Russian'}
    )

result = response.json()
print(result['text'])
```

**Ответ:**
```json
{
  "text": "Извлечённый текст из документа...",
  "model": "qwen3_vl_2b",
  "processing_time": 1.234,
  "image_size": [1920, 1080],
  "language": "Russian"
}
```

### Чат

#### POST /chat
Чат с моделью об изображении.

**Параметры:**
| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| file | File | Да | Изображение |
| prompt | string | Нет | Вопрос (по умолчанию: "Describe this image") |
| model | string | Нет | Модель (по умолчанию: qwen3_vl_2b) |
| temperature | float | Нет | Температура сэмплирования (0.0-1.0) |
| max_tokens | int | Нет | Максимум токенов для генерации |

**Пример с cURL:**
```bash
curl -X POST "http://localhost:8001/chat" \
  -F "file=@image.jpg" \
  -F "prompt=Что изображено на картинке?" \
  -F "model=qwen3_vl_2b"
```

**Пример с Python:**
```python
import requests

with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8001/chat',
        files={'file': f},
        data={
            'prompt': 'Опишите содержимое этого документа',
            'model': 'qwen3_vl_2b',
            'temperature': 0.7,
            'max_tokens': 512
        }
    )

result = response.json()
print(result['response'])
```

**Ответ:**
```json
{
  "response": "На изображении представлен...",
  "model": "qwen3_vl_2b",
  "processing_time": 2.567,
  "prompt": "Что изображено на картинке?"
}
```

### Пакетная обработка

#### POST /batch/ocr
Пакетная обработка нескольких изображений.

**Параметры:**
| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| files | File[] | Да | Список изображений (макс. 10) |
| model | string | Нет | Модель |

**Пример с cURL:**
```bash
curl -X POST "http://localhost:8001/batch/ocr" \
  -F "files=@doc1.jpg" \
  -F "files=@doc2.jpg" \
  -F "files=@doc3.jpg" \
  -F "model=qwen3_vl_2b"
```

**Пример с Python:**
```python
import requests

files = [
    ('files', open('doc1.jpg', 'rb')),
    ('files', open('doc2.jpg', 'rb')),
    ('files', open('doc3.jpg', 'rb'))
]

response = requests.post(
    'http://localhost:8001/batch/ocr',
    files=files,
    params={'model': 'qwen3_vl_2b'}
)

result = response.json()
print(f"Обработано: {result['successful']}/{result['total']}")

for item in result['results']:
    print(f"{item['filename']}: {item['text'][:100]}...")
```

**Ответ:**
```json
{
  "results": [
    {
      "filename": "doc1.jpg",
      "text": "Текст из первого документа...",
      "processing_time": 1.2,
      "status": "success"
    },
    {
      "filename": "doc2.jpg",
      "text": "Текст из второго документа...",
      "processing_time": 1.1,
      "status": "success"
    }
  ],
  "total": 3,
  "successful": 3,
  "failed": 0
}
```

### Управление моделями

#### DELETE /models/{model_name}
Выгрузка модели из памяти.

```bash
curl -X DELETE "http://localhost:8001/models/qwen3_vl_2b"
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Model qwen3_vl_2b unloaded"
}
```

## Безопасность и лимиты

### Rate Limiting

API ограничивает количество запросов на IP (по умолчанию 60 запросов/минуту, настраивается через переменную окружения `RATE_LIMIT`).

При превышении лимита возвращается:
```json
{
  "detail": "Превышен лимит запросов. Попробуйте через минуту."
}
```

Заголовки ответа содержат `X-RateLimit-Remaining` с количеством оставшихся запросов.

### Валидация файлов

- Максимальный размер файла: **10 MB** (413 при превышении)
- Максимум файлов в пакете: **10** (400 при превышении)
- Разрешённые расширения: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`, `.webp`
- Содержимое проверяется через PIL (не только расширение)

### CORS

Настраивается через переменную окружения `CORS_ORIGINS` (по умолчанию: `localhost:8501,localhost:3000`).

## Обработка ошибок

API возвращает стандартные HTTP коды ошибок:

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Неверный запрос (невалидный файл, слишком много файлов) |
| 404 | Ресурс не найден (модель не загружена) |
| 413 | Файл слишком большой (>10 MB) |
| 422 | Ошибка валидации параметров |
| 429 | Превышен лимит запросов (rate limiting) |
| 500 | Внутренняя ошибка сервера |

Пример ошибки:
```json
{
  "detail": "Недопустимое расширение файла. Разрешены: .jpg, .jpeg, .png, .bmp, .tiff, .tif, .webp"
}
```

## Рекомендации по использованию

### Выбор модели

| Задача | Рекомендуемая модель | Режим |
|--------|---------------------|-------|
| Быстрый OCR | qwen3_vl_2b | transformers (API) |
| Мультиязычный OCR (100+ языков) | dots_ocr | vLLM |
| Сложные макеты и таблицы | dots_ocr | vLLM |
| Чат и анализ документов | qwen3_vl_2b | transformers (API) |
| Тяжёлые задачи (7B) | qwen2_vl_7b | vLLM |

### Оптимизация производительности

1. **Предзагрузка моделей**: Первый запрос загружает модель, последующие быстрее
2. **Пакетная обработка**: Используйте `/batch/ocr` для нескольких файлов
3. **Размер изображений**: Оптимальный размер 1024-2048px по большей стороне
4. **Кеширование**: Модели кешируются между запросами

## Примеры интеграции

### Асинхронный клиент (aiohttp)

```python
import aiohttp
import asyncio

async def ocr_async(image_path: str) -> str:
    async with aiohttp.ClientSession() as session:
        with open(image_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename='image.jpg')
            
            async with session.post(
                'http://localhost:8001/ocr',
                data=data,
                params={'model': 'qwen3_vl_2b'}
            ) as response:
                result = await response.json()
                return result['text']

# Использование
text = asyncio.run(ocr_async('document.jpg'))
```

### Класс-обёртка

```python
import requests
from typing import Optional, List, Dict

class ChatVLMClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
    
    def health(self) -> Dict:
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def ocr(self, image_path: str, model: str = "qwen3_vl_2b", 
            language: Optional[str] = None) -> str:
        with open(image_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/ocr",
                files={'file': f},
                params={'model': model, 'language': language}
            )
        return response.json()['text']
    
    def chat(self, image_path: str, prompt: str, 
             model: str = "qwen3_vl_2b") -> str:
        with open(image_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/chat",
                files={'file': f},
                data={'prompt': prompt, 'model': model}
            )
        return response.json()['response']

# Использование
client = ChatVLMClient()
text = client.ocr('document.jpg', language='Russian')
answer = client.chat('diagram.png', 'Объясните эту диаграмму')
```
