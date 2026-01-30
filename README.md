# CHAT-VLM-LLM - OCR документов и Vision-Language модели

Комплексный инструментарий для OCR документов, визуального понимания и мультимодальных AI-приложений с использованием современных vision-language моделей.

## Возможности

### Поддерживаемые модели

#### Рабочие модели

- **Qwen3-VL 2B** - Основная рабочая модель, OCR на 32 языках, визуальный агент, контекст 256K
- **dots.ocr** - SOTA мультиязычный парсер документов (100+ языков)
- **Qwen3 Emergency Mode** - Аварийный режим загрузки Qwen3-VL

#### Экспериментальные (не работают)

- ~~Phi-3 Vision~~ - Microsoft, присутствует в transformers, но не функционирует
- ~~DeepSeek OCR~~ - Интеграция не завершена
- ~~GOT-OCR 2.0~~ - Требует доработки
- ~~Qwen2-VL~~ - Устаревшая версия

### Ключевые возможности

- **Мультиязычный OCR** - 32+ языка с высокой точностью
- **Визуальный агент** - Взаимодействие с GUI и автоматизация (Qwen3-VL)
- **Анализ документов** - Определение макета, извлечение таблиц, парсинг структуры
- **Понимание видео** - Контекст 256K для длинных видео
- **Гибкая квантизация** - Поддержка FP16, INT8, INT4
- **Flash Attention 2** - Быстрый инференс с меньшим потреблением памяти
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

| GPU | VRAM | Рекомендуемая модель | Статус |
|-----|------|---------------------|--------|
| RTX 5090 | 32GB | Qwen3-VL 2B@FP16 | Идеально |
| RTX 5080 | 16GB | Qwen3-VL 2B@FP16 | Отлично |
| RTX 5070 | 12GB | Qwen3-VL 2B@FP16 | Хорошо |
| RTX 4090 | 24GB | Qwen3-VL 2B@FP16 | Отлично |
| RTX 4080 | 16GB | Qwen3-VL 2B@INT8 | Хорошо |

## Структура проекта

```
CHAT-VLM-LLM/
├── models/
│   ├── base_model.py                   # Базовый класс моделей
│   ├── model_loader.py                 # Фабрика загрузки моделей
│   ├── model_loader_emergency.py       # Аварийный загрузчик Qwen3
│   ├── qwen3_vl.py                     # Qwen3-VL (рабочая)
│   ├── dots_ocr.py                     # dots.ocr (рабочая)
│   ├── dots_ocr_final.py               # dots.ocr финальная версия
│   ├── dots_ocr_vllm_integration.py    # Интеграция с vLLM
│   ├── got_ocr.py                      # GOT-OCR (не работает)
│   ├── qwen_vl.py                      # Qwen2-VL (устаревшая)
│   ├── deepseek_ocr.py                 # DeepSeek (не работает)
│   └── phi3_vision.py                  # Phi-3 (не работает)
├── .github/                            # GitHub workflows
├── Dockerfile                          # Docker образ
├── Dockerfile.light                    # Облегчённый образ
├── .env.example                        # Пример конфигурации
├── CHANGELOG.md                        # История изменений
├── CONTRIBUTING.md                     # Руководство контрибьютора
└── LICENSE                             # MIT лицензия
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
- **dots.ocr**: https://github.com/rednote-hilab/dots.ocr

---

**Рабочие модели: Qwen3-VL 2B, dots.ocr** | **Docker**
