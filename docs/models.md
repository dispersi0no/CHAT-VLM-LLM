# Документация по моделям

## Обзор поддерживаемых моделей

ChatVLMLLM поддерживает несколько vision-language моделей. Рабочие на данный момент: **Qwen3-VL 2B** и **dots.ocr**. Остальные находятся в экспериментальном состоянии.

## GOT-OCR 2.0 ⚠️ Экспериментальная

> **Статус:** Требует доработки интеграции. Не рекомендуется для продакшена.

### Описание
GOT-OCR 2.0 (General OCR Theory) — специализированная OCR модель от Stepfun AI.

### Характеристики

| Параметр | Значение |
|----------|----------|
| Параметры | 580M |
| VRAM (FP16) | 3 GB |
| Макс. токены | 4096 |
| Языки | 100+ |

### Сильные стороны
- Высокая точность на структурированных документах
- Извлечение таблиц
- Распознавание математических формул
- Сохранение форматирования

### Применение
- Научные статьи
- Финансовые документы
- Формы и таблицы
- Технические документы

### Использование

```python
from models import ModelLoader

model = ModelLoader.load_model('got_ocr')

# Базовый OCR
text = model.process_image(image)

# С указанием типа
text = model.process_image(image, ocr_type='format')
```

### Режимы OCR

| Режим | Описание |
|-------|----------|
| `ocr` | Простое извлечение текста |
| `format` | Сохранение форматирования |
| `multi-crop` | Для сложных макетов |

---

## Qwen2-VL 🟡 Нестабильная

> **Статус:** Qwen2-VL 2B доступна в обоих режимах. Qwen2-VL 7B — только через vLLM (в transformers режиме не работает стабильно).

### Описание
Qwen2-VL — vision-language модель от Alibaba Cloud с возможностями мультимодального понимания и чата.

### Варианты в config.yaml

| Модель | Режим | Параметры | VRAM (FP16) | Описание |
|--------|-------|-----------|-------------|----------|
| Qwen2-VL 2B (Transformers) | transformers | 2B | 4.7 GB | Лёгкая версия |
| Qwen2-VL 2B (vLLM) | vllm | 2B | 6.0 GB | Стабильная через vLLM |
| Qwen2-VL 7B (vLLM) | vllm | 7B | 16.0 GB | Только vLLM |

### Сильные стороны
- Мультимодальное понимание
- Контекстно-зависимые ответы
- Интерактивный чат
- Способности к рассуждению

### Применение
- Вопрос-ответ по документам
- Визуальный анализ
- Извлечение контента
- Описание изображений

### Использование

```python
from models import ModelLoader

# 2B версия
model = ModelLoader.load_model('qwen_vl_2b')

# 7B версия
model = ModelLoader.load_model('qwen_vl_7b')

# OCR
text = model.process_image(image, "Извлеките весь текст")

# Чат
response = model.chat(image, "Что изображено на этой картинке?")
```

---

## Qwen3-VL 🟢 Основная

> **Статус:** Рабочая, основная модель проекта.

### Описание
Qwen3-VL — новейшая серия VLM моделей с SOTA производительностью, расширенным OCR на 32 языках и возможностями визуального агента.

### Варианты в config.yaml

| Модель | Режим | Параметры | VRAM (FP16) |
|--------|-------|-----------|-------------|
| Qwen3-VL 2B (Transformers) | transformers | 2B | 4.4 GB |
| Qwen3-VL 2B (vLLM) | vllm | 2B | 6.5 GB |

### Ключевые улучшения (vs Qwen2-VL)
- OCR на 32 языках (было 19)
- Контекст 256K токенов (было 32K)
- Визуальный агент
- 3D пространственное восприятие
- Режим размышления
- Поддержка INT4 квантизации

### Поддерживаемые языки OCR
Английский, русский, немецкий, французский, испанский, итальянский, португальский, китайский (упр./трад.), японский, корейский, арабский, иврит, хинди, вьетнамский, тайский, индонезийский и другие.

### Применение
- Мультиязычный OCR
- Анализ документов
- Визуальный агент (GUI автоматизация)
- Понимание видео
- Сложные рассуждения

### Использование

```python
from models import ModelLoader

# Загрузка модели (Transformers режим)
model = ModelLoader.load_model('qwen3_vl_2b')

# OCR с указанием языка
text = model.extract_text(image, language='Russian')

# Анализ документа
analysis = model.analyze_document(image, focus='layout')

# Визуальное рассуждение
reasoning = model.visual_reasoning(image, "Объясните данные на графике")

# Чат
response = model.chat(image, "Какие выводы можно сделать?")
```

### Специальные методы

```python
# Извлечение текста
text = model.extract_text(image, language='Japanese')

# Анализ документа
# focus: 'general', 'layout', 'content', 'tables'
analysis = model.analyze_document(image, focus='tables')

# Визуальное рассуждение
reasoning = model.visual_reasoning(image, "Вопрос для анализа")
```

---

## Phi-3.5 Vision 🔵 vLLM

> **Статус:** Доступна только через vLLM бэкенд.

### Описание
Phi-3.5 Vision — продвинутая vision-language модель от Microsoft для сложных задач визуального анализа.

### Характеристики

| Параметр | Значение |
|----------|----------|
| Режим | vLLM |
| VRAM | 8 GB |
| Порт контейнера | 8002 |

### Применение
- Сложные задачи визуального анализа
- Понимание документов
- Описание и рассуждение

---

## dots.ocr 🟢 Рабочая

> **Статус:** Рабочая. Используется через vLLM бэкенд.

### Описание
dots.ocr — SOTA мультиязычный парсер документов от RedNote с поддержкой 100+ языков и унифицированным выходом.

### Характеристики

| Параметр | Значение |
|----------|----------|
| Параметры | 1.7B |
| VRAM (BF16) | 8 GB |
| Языки | 100+ |
| Макс. токены | 24000 |

### Сильные стороны
- 100+ языков
- Детекция макета
- Унифицированный JSON выход
- Извлечение формул (LaTeX)
- Извлечение таблиц (HTML)

### Режимы работы

| Режим | Описание |
|-------|----------|
| `layout_all` | Полный парсинг с детекцией и распознаванием |
| `layout_only` | Только детекция макета |
| `ocr_only` | Только распознавание текста |
| `grounding_ocr` | OCR с привязкой к bbox |

### Использование

```python
from models import ModelLoader

model = ModelLoader.load_model('dots_ocr')

# Полный парсинг документа
result = model.parse_document(image, return_json=True)

# Только OCR
text = model.process_image(image, mode='ocr_only')

# С указанием области
text = model.process_image(image, mode='grounding_ocr', bbox=[100, 100, 500, 500])
```

### Структура выхода

```json
{
  "layout": [
    {
      "bbox": [x1, y1, x2, y2],
      "category": "Title",
      "text": "Заголовок документа"
    },
    {
      "bbox": [x1, y1, x2, y2],
      "category": "Table",
      "text": "<table>...</table>"
    }
  ]
}
```

### Категории элементов
- Title — заголовок
- Section-header — заголовок раздела
- Text — обычный текст
- List-item — элемент списка
- Table — таблица (HTML)
- Formula — формула (LaTeX)
- Picture — изображение
- Caption — подпись
- Page-header — колонтитул
- Page-footer — нижний колонтитул
- Footnote — сноска

---

## Сравнение моделей

### Модели в config.yaml

| Модель | Режим | Параметры | VRAM | Статус |
|--------|-------|-----------|------|--------|
| Qwen3-VL 2B | transformers / vllm | 2B | 4.4–6.5 GB | 🟢 Основная |
| Qwen2-VL 2B | transformers / vllm | 2B | 4.7–6.0 GB | 🟡 Нестабильная |
| Qwen2-VL 7B | vllm | 7B | 16.0 GB | 🟡 Только vLLM |
| Phi-3.5 Vision | vllm | 3.8B | 8.0 GB | 🔵 vLLM |
| dots.ocr | vllm | 1.7B | 4.5 GB | 🟢 Рабочая |
| GOT-OCR 2.0 | transformers | 580M | 3 GB | ⚠️ Экспериментальная |

### Рекомендации по выбору

| Задача | Рекомендуемая модель |
|--------|---------------------|
| Быстрый OCR | Qwen3-VL 2B |
| Мультиязычный OCR (100+ языков) | dots.ocr |
| Сложные макеты и таблицы | dots.ocr |
| Чат и анализ | Qwen3-VL 2B |
| Сложный визуальный анализ | Phi-3.5 Vision (vLLM) |

## Загрузка моделей

### Через ModelLoader

```python
from models import ModelLoader

# С настройками по умолчанию
model = ModelLoader.load_model('qwen3_vl_2b')

# С параметрами
model = ModelLoader.load_model(
    'qwen3_vl_2b',
    precision='int8',
    use_flash_attention=True
)
```

### Ручная загрузка

```python
from transformers import AutoModel, AutoProcessor

model = AutoModel.from_pretrained(
    "Qwen/Qwen3-VL-2B-Instruct",
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
```

## Выгрузка моделей

```python
# Выгрузка конкретной модели
ModelLoader.unload_model('qwen3_vl_2b')

# Выгрузка всех моделей
ModelLoader.unload_all_models()

# Проверка загруженных
loaded = ModelLoader.get_loaded_models()
print(f"Загружены: {loaded}")
```
