# Требования к GPU

## Обзор

Это руководство поможет выбрать оптимальную модель для вашей видеокарты и настроить квантизацию для эффективного использования памяти.

## Таблица совместимости

### Потребление VRAM по моделям

| Модель | Режим | FP16 / BF16 | INT8 |
|--------|-------|-------------|------|
| GOT-OCR 2.0 | transformers | 3 GB | 2 GB |
| Qwen2-VL 2B | transformers | 4.7 GB | 3.6 GB |
| Qwen2-VL 2B | vllm | 6.0 GB | — |
| Qwen3-VL 2B | transformers | 4.4 GB | 2.2 GB |
| Qwen3-VL 2B | vllm | 6.5 GB | — |
| Phi-3.5 Vision | vllm | 8.0 GB | — |
| dots.ocr | vllm | 4.5 GB | — |
| Qwen2-VL 7B | vllm | 16.0 GB | — |

### Рекомендации по GPU

| VRAM | Рекомендуемые модели | Примечание |
|------|---------------------|------------|
| 4 GB | GOT-OCR (экспериментальная), Qwen3-VL 2B@INT8 | Только экспериментально |
| 6 GB | Qwen3-VL 2B (transformers), dots.ocr (vllm) | Стабильный вариант |
| 8 GB | Qwen2-VL 2B (transformers/vllm), Phi-3.5 (vllm) | Хороший баланс |
| 16 GB+ | Qwen2-VL 7B (vllm) | Тяжёлые задачи |
| 24 GB+ | Все модели | Без ограничений |

## Популярные видеокарты

### NVIDIA GeForce RTX 50-серия (2025)

| GPU | VRAM | Лучшие модели | Примечания |
|-----|------|---------------|------------|
| RTX 5090 | 32 GB | Все модели@FP16 | Без ограничений |
| RTX 5080 | 16 GB | Qwen2-VL 7B@vLLM | Оптимальный выбор |
| RTX 5070 Ti | 16 GB | Qwen2-VL 7B@vLLM | Отличная производительность |
| RTX 5070 | 12 GB | Phi-3.5@vLLM, dots.ocr@vLLM | Хороший баланс |
| RTX 5060 Ti | 16/8 GB | Зависит от версии | 16GB версия предпочтительна |

### NVIDIA GeForce RTX 40-серия

| GPU | VRAM | Лучшие модели |
|-----|------|---------------|
| RTX 4090 | 24 GB | Все модели@FP16 |
| RTX 4080 Super | 16 GB | Qwen2-VL 7B@vLLM |
| RTX 4080 | 16 GB | Qwen2-VL 7B@vLLM |
| RTX 4070 Ti Super | 16 GB | Qwen2-VL 7B@vLLM |
| RTX 4070 Ti | 12 GB | Phi-3.5@vLLM, dots.ocr@vLLM |
| RTX 4070 | 12 GB | Qwen3-VL 2B, dots.ocr@vLLM |
| RTX 4060 Ti | 16/8 GB | Qwen2-VL 2B, Qwen3-VL 2B |
| RTX 4060 | 8 GB | Qwen3-VL 2B@FP16, dots.ocr@vLLM |

### NVIDIA GeForce RTX 30-серия

| GPU | VRAM | Лучшие модели |
|-----|------|---------------|
| RTX 3090 | 24 GB | Все модели@FP16 |
| RTX 3080 Ti | 12 GB | Phi-3.5@vLLM, dots.ocr@vLLM |
| RTX 3080 | 10/12 GB | Qwen3-VL 2B@FP16, dots.ocr@vLLM |
| RTX 3070 Ti | 8 GB | Qwen3-VL 2B@FP16, dots.ocr@vLLM |
| RTX 3070 | 8 GB | Qwen3-VL 2B@FP16, dots.ocr@vLLM |
| RTX 3060 | 12 GB | Qwen2-VL 2B@FP16, dots.ocr@vLLM |

## Настройка квантизации

### FP16 (по умолчанию)

Максимальное качество, требует больше памяти.

```yaml
# config.yaml — transformers секция
transformers:
  qwen3_vl_2b:
    precision: "fp16"
```

```python
model = ModelLoader.load_model('qwen3_vl_2b', precision='fp16')
```

### INT8 (рекомендуется)

Хороший баланс качества и памяти. Снижение VRAM на ~40%.

```yaml
transformers:
  qwen3_vl_2b:
    precision: "int8"
```

```python
model = ModelLoader.load_model('qwen3_vl_2b', precision='int8')
```

### INT4 (максимальная экономия)

Минимальное потребление памяти. Снижение VRAM на ~66%.

```yaml
transformers:
  qwen3_vl_2b:
    precision: "int4"
```

```python
model = ModelLoader.load_model('qwen3_vl_2b', precision='int4')
```

## Flash Attention 2

Flash Attention 2 ускоряет инференс и снижает потребление памяти на 20-40%.

### Требования

- NVIDIA GPU с Compute Capability >= 8.0 (Ampere и новее)
- PyTorch 2.0+
- flash-attn >= 2.3.0

### Установка

```bash
pip install flash-attn --no-build-isolation
```

### Включение

```yaml
# config.yaml — transformers секция
transformers:
  qwen3_vl_2b:
    use_flash_attention: true
```

```python
model = ModelLoader.load_model('qwen3_vl_2b', use_flash_attention=True)
```

## Проверка GPU

### Скрипт проверки

```bash
python scripts/check_gpu.py
```

Вывод:
```
=== Проверка GPU ===
CUDA доступна: Да
GPU: NVIDIA GeForce RTX 4090
VRAM: 24.0 GB
Compute Capability: 8.9
Flash Attention: Поддерживается

=== Рекомендуемые модели ===
- Qwen3-VL 2B @ FP16 (4.4 GB)
- Qwen2-VL 2B @ FP16 (4.7 GB)
- dots.ocr @ BF16/vLLM (4.5 GB)
- GOT-OCR 2.0 @ FP16 (3 GB)
- Phi-3.5 Vision @ vLLM (8 GB)
```

### Программная проверка

```python
import torch

# Проверка CUDA
print(f"CUDA доступна: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    # Информация о GPU
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    
    # VRAM
    total_memory = torch.cuda.get_device_properties(0).total_memory
    print(f"VRAM: {total_memory / 1024**3:.1f} GB")
    
    # Compute Capability
    major, minor = torch.cuda.get_device_capability(0)
    print(f"Compute Capability: {major}.{minor}")
    
    # Flash Attention
    flash_attention_supported = major >= 8
    print(f"Flash Attention: {'Да' if flash_attention_supported else 'Нет'}")
```

## Оптимизация памяти

### Автоматическое распределение

```python
model = ModelLoader.load_model('qwen3_vl_2b', device_map='auto')
```

### Очистка кеша

```python
import torch

# Очистка CUDA кеша
torch.cuda.empty_cache()

# Выгрузка модели
ModelLoader.unload_model('qwen3_vl_2b')
```

### Мониторинг памяти

```python
import torch

# Текущее использование
allocated = torch.cuda.memory_allocated() / 1024**3
reserved = torch.cuda.memory_reserved() / 1024**3

print(f"Выделено: {allocated:.2f} GB")
print(f"Зарезервировано: {reserved:.2f} GB")
```

## Устранение проблем

### Out of Memory (OOM)

1. Используйте более агрессивную квантизацию (INT4)
2. Уменьшите размер изображений
3. Выгрузите неиспользуемые модели
4. Очистите CUDA кеш

### Медленный инференс

1. Включите Flash Attention 2
2. Используйте FP16 вместо FP32
3. Обновите драйверы NVIDIA
4. Проверьте термальный троттлинг

### Модель не загружается

1. Проверьте доступную VRAM
2. Используйте меньшую модель или квантизацию
3. Перезагрузите CUDA (`torch.cuda.empty_cache()`)
4. Перезапустите Python/Jupyter

## Сравнение производительности

### Время инференса (RTX 4090, изображение 1024x1024)

| Модель | Режим | FP16/BF16 |
|--------|-------|-----------|
| GOT-OCR 2.0 | transformers | 0.5s |
| Qwen2-VL 2B | transformers | 0.8s |
| Qwen3-VL 2B | transformers | 0.8s |
| dots.ocr | vllm | 1.2s |
| Phi-3.5 Vision | vllm | ~1.5s |
| Qwen2-VL 7B | vllm | ~2.0s |

### Качество OCR (CER, ниже лучше)

| Модель | FP16 | INT8 |
|--------|------|------|
| Qwen3-VL 2B | 3.1% | 3.3% |
| GOT-OCR 2.0 | 2.8% | 3.0% |
| dots.ocr | 2.3% | — |

*CER = Character Error Rate (частота ошибок на символ)*
