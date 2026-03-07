<div align="center">

# 🤖 CHAT-VLM-LLM

### Vision-Language Models & Document OCR Toolkit

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

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
│   ├── 🟢 qwen3_vl.py            # Qwen3-VL (рабочая)
│   ├── 🟢 dots_ocr.py            # dots.ocr (рабочая)
│   ├── 🟢 dots_ocr_final.py      # dots.ocr final
│   ├── ⬜ base_model.py          # Базовый класс
│   ├── ⬜ model_loader.py        # Загрузчик моделей
│   ├── 🟡 qwen_vl.py             # Qwen2-VL (нестабильна)
│   ├── 🔴 got_ocr.py             # GOT-OCR (не работает)
│   ├── 🔴 deepseek_ocr.py        # DeepSeek (не работает)
│   └── 🔴 phi3_vision.py         # Phi-3 (не работает)
├── 📂 utils/                      # Утилиты обработки
├── 📂 ui/                         # UI компоненты
├── 📂 tests/                      # Тесты
├── 📂 docs/                       # Документация
├── 📂 .github/                    # CI/CD workflows
├── 🐳 Dockerfile                  # Docker образ
├── 💨 Dockerfile.light            # Light версия
├── ⚙️ config.yaml                 # Конфигурация
├── 🚀 app.py                      # Streamlit приложение
├── 🔌 api.py                      # FastAPI REST API
└── 📄 LICENSE                     # MIT
```

---

## 🤝 Участие в разработке

Приветствуем вклад в проект! Смотрите [CONTRIBUTING.md](CONTRIBUTING.md)

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

**Сделано с ❤️ для сообщества AI**

🟢 **Qwen3-VL 2B** • 🟢 **dots.ocr** • 🐳 **Docker Ready**

</div>
