# Архитектура системы

## Обзор

ChatVLMLLM — это модульное исследовательское приложение для изучения Vision Language Models в задачах OCR документов. Архитектура следует паттерну многослойного проектирования с чётким разделением ответственности.

## Слои архитектуры

```
┌─────────────────────────────────────────┐
│       Клиентский слой                   │
│  - Streamlit UI (app.py)                │
│  - FastAPI REST API (api.py)            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Слой обработки (utils/)           │
│  - Предобработка изображений            │
│  - Извлечение и очистка текста          │
│  - Парсинг полей                        │
│  - Рендеринг контента                   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│        Слой моделей (models/)           │
│  - ModelLoader (фабрика)                │
│  - Загрузка и кеширование моделей       │
│  - Выполнение инференса                 │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│     Бэкенды инференса                   │
│  - Transformers (Qwen3-VL, GOT-OCR)     │
│  - vLLM (dots.ocr, Qwen-VL vLLM mode)   │
└─────────────────────────────────────────┘
```

## Детали компонентов

### 1. Клиентский слой

**Streamlit UI** (`app.py`):
- OCR интерфейс с загрузкой изображений
- Chat интерфейс с историей диалога
- Выбор и управление моделями
- Экспорт результатов (JSON, CSV, TXT)

**FastAPI REST API** (`api.py`):
- `POST /ocr` — извлечение текста из изображения
- `POST /chat` — чат с моделью об изображении
- `POST /batch/ocr` — пакетная обработка
- `GET /health` — статус сервиса и GPU
- `GET /models` — доступные модели
- `DELETE /models/{name}` — выгрузка модели

**UI компоненты** (`ui/`):
- `styles.py` — кастомные CSS стили
- `components.py` — переиспользуемые UI элементы

### 3. Слой обработки

**Технология:** Python, PIL, OpenCV, NumPy

**Компоненты:**

#### ImageProcessor (`utils/image_processor.py`)
- Предобработка изображений
- Изменение размера и нормализация
- Улучшение (контраст, резкость)
- Шумоподавление
- Выравнивание (deskew)
- Обрезка границ

#### TextExtractor (`utils/text_extractor.py`)
- Очистка и нормализация текста
- Извлечение сущностей (даты, email, телефоны)
- Сопоставление с шаблонами
- Оценка уверенности

#### FieldParser (`utils/field_parser.py`)
- Извлечение структурированных полей
- Парсинг по типам документов
- Извлечение пар ключ-значение

#### MarkdownRenderer (`utils/markdown_renderer.py`)
- Форматирование результатов
- Генерация таблиц
- Подсветка

**Ответственность:**
- Подготовка изображений для инференса
- Очистка и структурирование выхода OCR
- Извлечение конкретной информации
- Форматирование результатов для отображения

### 4. Слой моделей

**Технология:** PyTorch, Transformers

**Компоненты:**

#### BaseModel (`models/base_model.py`)
- Абстрактный базовый класс
- Общий интерфейс
- Общие утилиты

#### GOTOCRModel (`models/got_ocr.py`)
- Интеграция GOT-OCR 2.0
- OCR-специфичные методы
- Сохранение форматирования

#### QwenVLModel (`models/qwen_vl.py`)
- Интеграция Qwen2-VL
- Возможности чата
- Мультимодальное понимание

#### Qwen3VLModel (`models/qwen3_vl.py`)
- Интеграция Qwen3-VL
- Расширенный OCR (32 языка)
- Визуальный агент

#### DotsOCRModel (`models/dots_ocr.py`)
- Интеграция dots.ocr
- Парсинг макета документов
- Мультиязычная поддержка

#### ModelLoader (`models/model_loader.py`)
- Паттерн Фабрика для создания моделей
- Управление жизненным циклом моделей
- Обработка конфигурации
- Кеширование загруженных моделей

**Ответственность:**
- Загрузка и инициализация моделей
- Выполнение инференса
- Управление памятью GPU
- Предоставление унифицированного API

## Поток данных

### Рабочий процесс OCR

```
Загрузка пользователем
    ↓
Валидация изображения
    ↓
Предобработка
  - Изменение размера
  - Улучшение
  - Шумоподавление
    ↓
Выбор модели
    ↓
Инференс
  - GOT-OCR, Qwen3-VL или dots.ocr
    ↓
Постобработка
  - Очистка текста
  - Извлечение полей
    ↓
Форматирование результата
  - Markdown рендеринг
  - Генерация таблиц
    ↓
Отображение пользователю
    ↓
Опции экспорта
  - JSON
  - CSV
  - Текст
```

### Рабочий процесс чата

```
Загрузка изображения
    ↓
Предобработка изображения
    ↓
Сообщение пользователя
    ↓
Построение контекста
  - Контекст изображения
  - История чата
    ↓
Инференс модели
  - Qwen-VL
    ↓
Генерация ответа
    ↓
Markdown рендеринг
    ↓
Отображение с историей
    ↓
Продолжение диалога
```

## Управление конфигурацией

**Файл:** `config.yaml`

**Структура:**
```yaml
# Transformers режим — стабильные модели (CPU/GPU, прямая загрузка)
transformers:
  qwen_vl_2b:
    name: Qwen2-VL 2B (Transformers)
    model_path: Qwen/Qwen2-VL-2B-Instruct
    precision: fp16
    device_map: auto
    max_new_tokens: 2048
    # ... другие параметры

  qwen3_vl_2b:
    name: Qwen3-VL 2B (Transformers)
    model_path: Qwen/Qwen3-VL-2B-Instruct
    precision: fp16
    device_map: auto
    # ... другие параметры

# vLLM режим — сервер инференса через Docker-контейнеры
vllm:
  dots_ocr:
    model_path: rednote-hilab/dots.ocr
    port: 8000
    memory_gb: 4.5
    # ...

  qwen2_vl_2b:
    model_path: Qwen/Qwen2-VL-2B-Instruct
    port: 8001
    memory_gb: 6.0
    # ...

  phi35_vision:
    model_path: microsoft/Phi-3.5-vision-instruct
    port: 8002
    memory_gb: 8.0
    # ...

  qwen2_vl_7b:
    model_path: Qwen/Qwen2-VL-7B-Instruct
    port: 8003
    memory_gb: 16.0
    # ...

  qwen3_vl_2b:
    model_path: Qwen/Qwen3-VL-2B-Instruct
    port: 8004
    memory_gb: 6.5
    # ...

ocr:
  supported_formats: [jpg, jpeg, png, bmp, tiff]
  max_image_size: байты
  resize_max_dimension: пиксели

document_templates:
  document_type:
    fields: [поле1, поле2, ...]
```

## Управление состоянием

**Streamlit Session State:**

```python
st.session_state = {
    "loaded_model": None,
    "chat_history": [],
    "uploaded_image": None,
    "ocr_result": None,
    "extracted_fields": {},
}
```

## Обработка ошибок

**Стратегия:**
- Try-except блоки на каждом слое
- Понятные сообщения для пользователя
- Логирование для отладки
- Graceful degradation

**Пример:**
```python
try:
    result = model.process_image(image)
except torch.cuda.OutOfMemoryError:
    st.error("Недостаточно памяти GPU. Попробуйте меньшее изображение или модель.")
except Exception as e:
    st.error(f"Ошибка обработки: {str(e)}")
    logger.exception("Ошибка инференса модели")
```

## Оптимизации производительности

### Кеширование

```python
@st.cache_resource
def load_model(model_key):
    return ModelLoader.load_model(model_key)

@st.cache_data
def preprocess_image(image_bytes):
    return ImageProcessor.preprocess(image_bytes)
```

### Управление памятью

- Ленивая загрузка моделей
- Явная очистка памяти GPU
- Выгрузка моделей при переключении
- Оптимизация пакетной обработки

### Оптимизация инференса

- Flash Attention 2 (при наличии)
- Mixed precision (FP16)
- Квантизация (INT8/INT4)
- Device mapping (auto)

## Безопасность

### Валидация входных данных

```python
# Лимиты размера файла
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Валидация формата
ALLOWED_FORMATS = ["jpg", "jpeg", "png", "bmp"]

# Санитизация ввода
def sanitize_prompt(prompt: str) -> str:
    return prompt.strip()[:500]
```

### Лимиты ресурсов

- Максимальные размеры изображения
- Лимиты генерации токенов
- Таймаут инференса
- Rate limiting (при развёртывании)

## Стратегия тестирования

### Модульные тесты

```python
# tests/test_models.py
def test_model_loading():
    model = ModelLoader.load_model("got_ocr")
    assert model is not None

# tests/test_utils.py
def test_image_preprocessing():
    image = Image.open("test.jpg")
    processed = ImageProcessor.preprocess(image)
    assert processed.size[0] <= 2048
```

### Интеграционные тесты

- End-to-end OCR workflow
- Поток чат-диалога
- Переключение моделей

## Развёртывание

### Docker

Проект поставляется с несколькими Docker-конфигурациями:

| Файл | Назначение |
|------|------------|
| `Dockerfile` | Полный образ (Streamlit + FastAPI, CUDA cu126) |
| `Dockerfile.light` | Облегчённый образ без GPU-зависимостей |
| `docker-compose.yml` | Стандартный стек (Streamlit + Nginx) |
| `docker-compose-vllm.yml` | vLLM стек с отдельными контейнерами для каждой модели |

**Запуск стандартного стека:**
```bash
docker compose up -d
```

**Запуск vLLM стека:**
```bash
docker compose -f docker-compose-vllm.yml up -d
```

Nginx (`nginx.conf`) используется как reverse proxy перед Streamlit-приложением.

### Требования к ресурсам

**Минимальные:**
- 8GB RAM
- 4GB VRAM (для малых моделей)
- 2 CPU ядра

**Рекомендуемые:**
- 16GB RAM
- 16GB VRAM (для больших моделей)
- 4+ CPU ядра
- SSD накопитель

## Паттерны проектирования

| Паттерн | Применение | Компонент |
|---------|------------|-----------|
| Factory | Создание моделей | ModelLoader |
| Strategy | Унифицированный интерфейс моделей | BaseModel |
| Template Method | Общая структура обработки | BaseModel |
| Singleton | Кеш загруженных моделей | ModelLoader |
| Adapter | Интеграция внешних моделей | GOTOCRModel, QwenVLModel |

## Планы развития

### Запланированные возможности

1. **Fine-tuning**: Обучение на своих данных
2. **PDF поддержка**: Полная обработка PDF документов
3. **Облачное развёртывание**: AWS/GCP хостинг
4. **Аутентификация**: Учётные записи и права доступа
5. **База результатов**: Хранение и поиск прошлых результатов

### Эволюция архитектуры

- Микросервисная архитектура для масштабирования
- Очередь сообщений для асинхронной обработки
- Распределённый инференс моделей
- CDN для статических ресурсов
