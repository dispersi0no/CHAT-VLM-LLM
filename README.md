<div align="center">

# 🤖 CHAT-VLM-LLM

### Vision-Language Models & Document OCR Toolkit

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/dispersi0no/CHAT-VLM-LLM/ci.yml?style=for-the-badge&label=CI)](https://github.com/dispersi0no/CHAT-VLM-LLM/actions/workflows/ci.yml)

<p align="center">
  <b>Комплексный инструментарий для OCR документов и мультимодальных AI-приложений</b>
</p>

---

[🚀 Быстрый старт](#-быстрый-старт) •
[📦 Модели](#-поддерживаемые-модели) •
[🐳 Docker](#-docker) •
[📊 GPU](#-требования-к-gpu)

</div>

---

## ✨ Возможности

<table>
<tr>
<td width="50%">

### 🎯 Основные
- 🌐 **Мультиязычный OCR** — 32+ языка
- 🤖 **Визуальный агент** — GUI автоматизация
- 📄 **Анализ документов** — таблицы, структура
- 🎬 **Понимание видео** — контекст 256K

</td>
<td width="50%">

### ⚡ Производительность
- 🚀 **Flash Attention 2** — быстрый инференс
- 📦 **Квантизация** — FP16, INT8, INT4
- 🐳 **Docker** — GPU контейнеры
- 🟢 **Blackwell** — NVIDIA оптимизация

</td>
</tr>
</table>

---

## 📦 Поддерживаемые модели

### ✅ Рабочие

| Модель | Описание | Статус |
|--------|----------|--------|
| **Qwen3-VL 2B** | OCR на 32 языках, визуальный агент, контекст 256K (включая Emergency Mode) | 🟢 Основная |
| **dots.ocr** | SOTA парсер документов, 100+ языков | 🟢 Работает |

### ⚠️ Экспериментальные (не работают)

| Модель | Проблема | Статус |
|--------|----------|--------|
| Phi-3 Vision | Microsoft, есть только в vLLM, не функционирует | 🔴 Не работает |
| DeepSeek OCR | Интеграция не завершена | 🔴 Не работает |
| GOT-OCR 2.0 | Требует доработки | 🔴 Не работает |
| Qwen2-VL | Нестабильная, не доработана | 🟡 Нестабильна |

---

## 🏗️ Архитектура моделей

Все модели наследуют от `BaseModel` (ABC):

```
BaseModel (abstract)
├── _get_device()          # Auto-detect CUDA/MPS/CPU
├── _get_load_kwargs()     # dtype + device_map
├── extract_fields()       # JSON field extraction
├── run()                  # Unified inference entry point
├── unload()               # GPU memory cleanup
├── load() *abstract*
└── inference() *abstract*
    ┃
    ├── Qwen3VLModel       # Qwen3-VL 2B
    ├── DotsOCRModel       # dots.ocr
    ├── QwenVLModel        # Qwen2-VL
    └── GOTOCRModel        # GOT-OCR 2.0
```

---

## 🚀 Быстрый старт

### Установка

```bash
# Клонирование
git clone https://github.com/dispersi0no/CHAT-VLM-LLM.git
cd CHAT-VLM-LLM

# Зависимости
pip install -r requirements.txt
```

### Конфигурация

```bash
cp .env.example .env
# Отредактируйте .env под свои нужды
```

---

## 🐳 Docker

```bash
# 📦 Стандартная сборка
docker build -t chat-vlm-llm .

# 💨 Облегчённая версия
docker build -f Dockerfile.light -t chat-vlm-llm-light .

# ▶️ Запуск
docker-compose up -d
```

---

## 🧪 Разработка

### Тестирование
```bash
pytest tests/ -v
```

### Линтинг
```bash
black . && isort .
```

### CI
При каждом push/PR автоматически запускаются:
- ✅ black (форматирование)
- ✅ isort (сортировка импортов)
- ✅ pytest на Python 3.10, 3.11, 3.12

---

## 📊 Требования к GPU

| GPU | VRAM | Рекомендация | Статус |
|:---:|:----:|:---------------:|:------:|
| **RTX 5090** | 32GB | Qwen3-VL 2B @ FP16 | 🟢 Идеально |
| **RTX 5080** | 16GB | Qwen3-VL 2B @ FP16 | 🟢 Отлично |
| **RTX 4090** | 24GB | Qwen3-VL 2B @ FP16 | 🟢 Отлично |
| **RTX 4080** | 16GB | Qwen3-VL 2B @ INT8 | 🟡 Хорошо |
| **RTX 3090** | 24GB | Qwen3-VL 2B @ FP16 | 🟡 Хорошо |

---

## 📁 Структура проекта

```
📂 CHAT-VLM-LLM/
├── 📂 models/
│   ├── ⬜ __init__.py
│   ├── ⬜ base_model.py           # Abstract base — device, unload, extract_fields
│   ├── 🟢 qwen3_vl.py            # Qwen3-VL 2B (основная)
│   ├── 🟢 dots_ocr.py            # dots.ocr parser
│   ├── 🟡 qwen_vl.py             # Qwen2-VL (нестабильна)
│   ├── 🔴 got_ocr.py             # GOT-OCR 2.0 (не работает)
│   ├── ⬜ model_loader.py        # Фабрика загрузки моделей
│   └── 📂 experimental/          # Экспериментальные модели
├── 📂 utils/                      # Утилиты обработки
├── 📂 ui/                         # Streamlit UI компоненты
│   ├── 📂 pages/                  # Страницы (home, chat, ocr, docs)
│   ├── sidebar.py                 # Боковая панель
│   ├── components.py              # Переиспользуемые компоненты
│   ├── message_renderer.py        # Рендер сообщений чата
│   ├── bbox_display.py            # Отображение bounding boxes
│   └── styles.py                  # CSS стили
├── 📂 tests/                      # Pytest тесты
├── 📂 docs/                       # Документация
├── 📂 .github/workflows/          # CI/CD (black, isort, pytest)
├── 🐳 Dockerfile                  # Docker образ
├── 💨 Dockerfile.light            # Light версия
├── ⚙️ config.yaml                 # Конфигурация моделей
├── 🚀 app.py                      # Streamlit приложение
├── 🔌 api.py                      # FastAPI REST API
├── 📄 requirements.txt            # Зависимости
└── 📄 LICENSE                     # MIT
```

---

## 🤝 Участие в разработке

Приветствуем вклад в проект! Смотрите [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📚 Ссылки

<table>
<tr>
<td align="center">
<a href="https://github.com/QwenLM/Qwen3-VL">
<img src="https://img.shields.io/badge/Qwen3--VL-GitHub-blue?style=for-the-badge&logo=github" />
</a>
</td>
<td align="center">
<a href="https://github.com/rednote-hilab/dots.ocr">
<img src="https://img.shields.io/badge/dots.ocr-GitHub-blue?style=for-the-badge&logo=github" />
</a>
</td>
</tr>
</table>

---

## 📄 Лицензия

Этот проект распространяется под лицензией [MIT](LICENSE)

---

<div align="center">

[![CI](https://img.shields.io/github/actions/workflow/status/dispersi0no/CHAT-VLM-LLM/ci.yml?style=for-the-badge&label=CI)](https://github.com/dispersi0no/CHAT-VLM-LLM/actions/workflows/ci.yml)

</div>
