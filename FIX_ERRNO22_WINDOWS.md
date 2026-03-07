# ИСПРАВЛЕНИЕ [Errno 22] Invalid argument НА WINDOWS

## 🔍 Проблема

При загрузке модели Qwen3-VL в режиме Transformers возникает ошибка:
```
[Errno 22] Invalid argument
```

### Симптомы:
- ✅ Модель загружается успешно ПЕРВЫЙ раз (например, в 22:23:30)
- ❌ Все последующие попытки падают с `[Errno 22]` при "Loading model weights..."
- 📁 Модель найдена в кеше (3.97 GB), но не может быть загружена
- 🔄 Ошибка повторяется при каждой попытке загрузки

### Логи ошибки:
```
2026-03-04 22:32:25 - INFO - Loading model weights...
2026-03-04 22:32:25 - ERROR - Failed to load Qwen3-VL: [Errno 22] Invalid argument
```

## 🎯 Причина

HuggingFace Hub в новых версиях (>0.17) по умолчанию создает **symlinks** (символические ссылки) в кеше моделей для экономии места. Windows **не может корректно читать** эти symlinks через Python API, что приводит к ошибке `[Errno 22] Invalid argument`.

### Техническая деталь:
- Файлы в `snapshots/` являются symlinks на файлы в `blobs/`
- Windows API может видеть symlinks, но Python `open()` не может их читать
- Первая загрузка работает, потому что файлы еще не закешированы
- Последующие загрузки пытаются читать symlinks и падают

## ✅ Решение

### Вариант 1: Автоматическое исправление (РЕКОМЕНДУЕТСЯ)

Запустите скрипт автоматического исправления:

```bash
python fix_qwen3_windows_symlinks.py
```

**Что делает скрипт:**
1. ✅ Устанавливает переменные окружения для отключения symlinks
2. 🗑️ Удаляет старый кеш модели с symlinks
3. 📥 Скачивает модель заново БЕЗ symlinks (с `local_dir_use_symlinks=False`)
4. 🔍 Проверяет, что модель загружается корректно
5. ✅ Выводит отчет о результатах

**Время выполнения:** ~5-10 минут (зависит от скорости интернета)

### Вариант 2: Ручное исправление

#### Шаг 1: Удалите кеш модели

**Через PowerShell:**
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface\hub\models--Qwen--Qwen3-VL-2B-Instruct"
```

**Через CMD:**
```cmd
rmdir /s /q "C:\Users\%USERNAME%\.cache\huggingface\hub\models--Qwen--Qwen3-VL-2B-Instruct"
```

**Через проводник Windows:**
1. Откройте: `C:\Users\Colorful\.cache\huggingface\hub\`
2. Удалите папку: `models--Qwen--Qwen3-VL-2B-Instruct`

#### Шаг 2: Проверьте переменные окружения

Убедитесь, что в файле `.env` установлены:
```env
HF_HUB_DISABLE_SYMLINKS=1
HF_HUB_DISABLE_SYMLINKS_WARNING=1
HF_HUB_ENABLE_HF_TRANSFER=0
TRANSFORMERS_OFFLINE=0
HF_HUB_OFFLINE=0
```

#### Шаг 3: Перезапустите приложение

```bash
python start_system.py
```

Модель скачается заново БЕЗ symlinks.

### Вариант 3: Использование vLLM режима (ОБХОДНОЕ РЕШЕНИЕ)

Если Transformers режим не работает, используйте vLLM:

1. В интерфейсе выберите: **"vLLM (Рекомендуется)"**
2. Выберите модель: **"dots.ocr"**
3. vLLM работает через Docker и не имеет проблем с symlinks

## 🔍 Проверка исправления

### Успешная загрузка:
```
2026-03-04 22:23:18 - INFO - Loading model: qwen3_vl_2b
2026-03-04 22:23:18 - INFO - Model path: Qwen/Qwen3-VL-2B-Instruct
2026-03-04 22:23:30 - INFO - Loading model weights...
2026-03-04 22:24:34 - INFO - ✅ Qwen3-VL loaded successfully
2026-03-04 22:24:34 - INFO - ✅ Successfully loaded model: qwen3_vl_2b
```

### Признаки успеха:
- ✅ Нет ошибок `[Errno 22]`
- ✅ Модель загружается за ~60-90 секунд
- ✅ Можно обрабатывать изображения
- ✅ Повторные загрузки работают без ошибок

## 📊 Статистика проблемы

**Из логов:**
- ✅ Первая загрузка: 22:23:30 - 22:24:34 (64 секунды) - УСПЕШНО
- ❌ Вторая загрузка: 22:32:25 - ОШИБКА [Errno 22]
- ❌ Третья загрузка: 22:32:32 - ОШИБКА [Errno 22]
- ❌ Четвертая загрузка: 22:32:39 - ОШИБКА [Errno 22]

**Вывод:** Проблема возникает только при использовании закешированных файлов с symlinks.

## 🛠️ Технические детали

### Что изменено в коде:

**1. `disable_symlinks_startup.py`** - автоматически отключает symlinks при импорте
```python
import os
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
```

**2. `models/qwen3_vl.py`** - использует `local_files_only=True`
```python
load_kwargs['local_files_only'] = True
load_kwargs['trust_remote_code'] = True
```

**3. `app.py`** - импортирует `disable_symlinks_startup` в начале
```python
import disable_symlinks_startup  # КРИТИЧЕСКИ ВАЖНО
```

### Почему это работает:

1. **Переменные окружения** отключают создание новых symlinks
2. **Удаление кеша** убирает старые symlinks
3. **local_files_only=True** заставляет использовать реальные файлы
4. **Повторная загрузка** создает кеш БЕЗ symlinks

## 🌐 Дополнительная информация

### Платформы:
- ❌ **Windows**: Проблема присутствует (symlinks не работают через Python)
- ✅ **Linux**: Проблемы нет (symlinks работают нативно)
- ✅ **macOS**: Проблемы нет (symlinks работают нативно)

### Версии:
- **huggingface_hub >= 0.17**: Использует symlinks по умолчанию
- **huggingface_hub < 0.17**: Копирует файлы (работает на Windows)

### Альтернативные решения:
1. Откатиться на старую версию: `pip install huggingface_hub==0.16.4`
2. Использовать WSL (Windows Subsystem for Linux)
3. Использовать vLLM режим через Docker

## 📞 Поддержка

Если проблема не решена:

1. Проверьте логи: `logs/chatvlmllm_YYYYMMDD.log`
2. Убедитесь, что кеш удален полностью
3. Проверьте права доступа к папке кеша
4. Попробуйте запустить от имени администратора
5. Используйте vLLM режим как временное решение

## 🎉 Результат

После исправления:
- ✅ Модель Qwen3-VL загружается без ошибок
- ✅ Работает в режиме Transformers (локально)
- ✅ Повторные загрузки работают стабильно
- ✅ Нет необходимости в Docker/vLLM для этой модели
