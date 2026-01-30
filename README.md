# CHAT-VLM-LLM - OCR документов и Vision-Language модели

Комплексный инструментарий для OCR документов, визуального понимания и мультимодальных AI-приложений с использованием современных vision-language моделей.

## Возможности

### Поддерживаемые модели

- **GOT-OCR 2.0** - Специализированный OCR для сложных макетов
- **Qwen2-VL** (2B, 7B) - Продвинутое vision-language понимание
- **Qwen3-VL** (2B, 4B, 8B) - Новейшая VLM с OCR на 32 языках, визуальным агентом, контекстом 256K
- **dots.ocr** - SOTA мультиязычный парсер документов (100+ языков)
- **DeepSeek OCR** - Интеграция DeepSeek для OCR задач
- **Phi-3 Vision** - Microsoft Phi-3 для визуальных задач

### Ключевые возможности

- **Мультиязычный OCR** - 32+ языка с высокой точностью
- **Визуальный агент** - Взаимодействие с GUI и автоматизация (Qwen3-VL)
- **Анализ документов** - Определение макета, извлечение таблиц, парсинг структуры
- **Визуальное рассуждение** - Сложные рассуждения об изображениях и диаграммах
- **Понимание видео** - Контекст 256K для длинных видео
- **Гибкая квантизация** - Поддержка FP16, INT8, INT4
- **Flash Attention 2** - Быстрый инференс с меньшим потреблением памяти
- **REST API** - Production-ready FastAPI эндпоинты
- **Docker** - Контейнеризация с поддержкой GPU
- **Blackwell GPU** - Оптимизация для NVIDIA Blackwell архитектуры

## Быстрый старт

### Установка

```bash
# Клонирование репозитория
git clone https://github.com/dispersi0no/CHAT-VLM-LLM.git
cd CHAT-VLM-LLM

# Установка зависимостей
pip install -r requirements.txt
```

### Docker

```bash
# Стандартная сборка
docker build -t chat-vlm-llm .

# Облегчённая версия
docker build -f Dockerfile.light -t chat-vlm-llm-light .

# Запуск
docker-compose up -d
```

## Требования к GPU

| GPU | VRAM | Лучшая модель | Статус |
|-----|------|---------------|--------|
| RTX 5090 | 32GB | Qwen3-VL 8B@FP16 | Идеально |
| RTX 5080 | 16GB | Qwen3-VL 8B@INT8 | Отлично |
| RTX 5070 | 12GB | Qwen3-VL 4B@FP16 | Хорошо |
| RTX 4090 | 24GB | Qwen3-VL 8B@FP16 | Отлично |
| RTX 4080 | 16GB | Qwen3-VL 8B@INT8 | Хорошо |

## Структура проекта

```
CHAT-VLM-LLM/
├── models/
│   ├── base_model.py           # Базовый класс моделей
│   ├── model_loader.py         # Фабрика загрузки моделей
│   ├── got_ocr.py              # GOT-OCR 2.0
│   ├── qwen_vl.py              # Qwen2-VL
│   ├── qwen3_vl.py             # Qwen3-VL
│   ├── dots_ocr.py             # dots.ocr
│   ├── deepseek_ocr.py         # DeepSeek OCR
│   └── phi3_vision.py          # Phi-3 Vision
├── .github/                    # GitHub workflows
├── Dockerfile                  # Docker образ
├── Dockerfile.light            # Облегчённый образ
├── .env.example                # Пример конфигурации
├── CHANGELOG.md                # История изменений
├── CONTRIBUTING.md             # Руководство контрибьютора
└── LICENSE                     # MIT лицензия
```

## Конфигурация

Скопируйте `.env.example` в `.env` и настройте параметры:

```bash
cp .env.example .env
```

## Участие в разработке

Приветствуем вклад в проект! См. [CONTRIBUTING.md](CONTRIBUTING.md).

## Лицензия

MIT License - см. [LICENSE](LICENSE)

## Ссылки

- **Qwen3-VL**: https://github.com/QwenLM/Qwen3-VL
- **GOT-OCR**: https://github.com/Ucas-HaoranWei/GOT-OCR2.0
- **dots.ocr**: https://github.com/rednote-hilab/dots.ocr

---

**Production Ready** | **6+ моделей** | **REST API** | **Docker**
