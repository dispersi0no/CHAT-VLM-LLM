"""Documentation page for ChatVLMLLM Streamlit application."""

import streamlit as st


def show_docs() -> None:
    """Render the 📚 Документация page."""
    st.header("📚 Документация")

    doc_tabs = st.tabs(["🚀 Быстрый старт", "🤖 Модели", "🏗️ Архитектура", "📖 API", "🤝 Участие"])

    with doc_tabs[0]:
        st.markdown("""
        ## Руководство по быстрому старту
        
        ### Установка
        
        ```bash
        # Клонировать репозиторий
        git clone https://github.com/dispersi0no/CHAT-VLM-LLM.git
        cd chatvlmllm
        
        # Настройка (автоматизированная)
        bash scripts/setup.sh  # Linux/Mac
        scripts\\setup.bat      # Windows
        
        # Запуск приложения
        streamlit run app.py
        ```
        
        ### Первые шаги
        
        1. ✅ Выберите модель в боковой панели
        2. 📄 Выберите режим OCR или чата
        3. 📤 Загрузите ваш документ
        4. 🚀 Получите мгновенные результаты!
        
        ### Выбор модели
        
        - **GOT-OCR**: Быстрое, точное извлечение текста
        - **Qwen2-VL 2B**: Легкий мультимодальный чат
        - **Qwen3-VL 2B**: Продвинутый анализ документов с поддержкой 32 языков
        - **Phi-3.5 Vision**: Мощная модель Microsoft для визуального анализа
        - **dots.ocr**: Специализированный парсер документов
        """)
        
        st.info("📖 Для подробных инструкций см. [QUICKSTART.md](https://github.com/dispersi0no/CHAT-VLM-LLM/blob/main/QUICKSTART.md)")

    with doc_tabs[1]:
        st.markdown("""
        ## Поддерживаемые модели
        
        ### GOT-OCR 2.0
        
        Специализированная OCR модель для сложных макетов документов.
        
        **Сильные стороны:**
        - ✅ Высокая точность на структурированных документах
        - ✅ Извлечение таблиц
        - ✅ Распознавание математических формул
        - ✅ Поддержка множества языков (100+ языков)
        
        **Случаи использования:**
        - Научные статьи
        - Финансовые документы
        - Формы и таблицы
        
        ### Qwen3-VL
        
        Модели машинного зрения общего назначения с улучшенными возможностями OCR.
        
        **Сильные стороны:**
        - ✅ Мультимодальное понимание
        - ✅ Контекстно-зависимые ответы
        - ✅ Интерактивный чат
        - ✅ Возможности рассуждения
        - ✅ Поддержка 32 языков OCR
        
        **Случаи использования:**
        - Вопросы и ответы по документам
        - Визуальный анализ
        - Извлечение контента
        
        ### Phi-3.5 Vision
        
        Мощная модель Microsoft для визуального анализа.
        
        **Сильные стороны:**
        - ✅ Высокое качество понимания изображений
        - ✅ Эффективная архитектура
        - ✅ Хорошая производительность на визуальных задачах
        
        ### dots.ocr
        
        Специализированный парсер документов для сложных макетов.
        
        **Сильные стороны:**
        - ✅ Понимание структуры документа
        - ✅ Извлечение макета
        - ✅ Поддержка множества языков
        - ✅ JSON вывод
        """)
        
        st.info("📖 Для подробной документации см. [docs/models.md](https://github.com/dispersi0no/CHAT-VLM-LLM/blob/main/docs/models.md)")

    with doc_tabs[2]:
        st.markdown("""
        ## Архитектура системы
        
        ### Слоистый дизайн
        
        ```
        UI слой (Streamlit)
              ↓
        Слой приложения
              ↓
        Слой обработки (Utils)
              ↓
        Слой моделей (VLM модели)
              ↓
        Основа (PyTorch/HF)
        ```
        
        ### Ключевые компоненты
        
        - **Модели**: Интеграция VLM и инференс
        - **Утилиты**: Обработка изображений и извлечение текста
        - **UI**: Интерфейс Streamlit и стилизация
        - **Тесты**: Обеспечение качества
        """)
        
        st.info("📖 Для деталей архитектуры см. [docs/architecture.md](https://github.com/dispersi0no/CHAT-VLM-LLM/blob/main/docs/architecture.md)")

    with doc_tabs[3]:
        st.markdown("""
        ## Справочник API
        
        ### Загрузка моделей
        
        ```python
        from models import ModelLoader
        
        # Загрузить модель
        model = ModelLoader.load_model('got_ocr')
        
        # Обработать изображение
        from PIL import Image
        image = Image.open('document.jpg')
        text = model.process_image(image)
        ```
        
        ### Извлечение полей
        
        ```python
        from utils.field_parser import FieldParser
        
        # Парсинг счета
        fields = FieldParser.parse_invoice(text)
        print(fields['invoice_number'])
        ```
        
        ### Интерфейс чата
        
        ```python
        # Интерактивный чат
        model = ModelLoader.load_model('qwen3_vl_2b')
        response = model.chat(image, "Что в этом документе?")
        ```
        """)

    with doc_tabs[4]:
        st.markdown("""
        ## Участие в проекте
        
        Мы приветствуем вклад! 🎉
        
        ### Как внести вклад
        
        1. 🍴 Сделайте форк репозитория
        2. 🌿 Создайте ветку функции
        3. ✍️ Внесите изменения
        4. ✅ Напишите тесты
        5. 📝 Обновите документацию
        6. 🚀 Отправьте pull request
        
        ### Области для вклада
        
        - 🐛 Исправления ошибок
        - ✨ Новые функции
        - 📝 Документация
        - 🧪 Тесты
        - 🎨 Улучшения UI
        """)
        
        st.info("📖 Для руководящих принципов участия см. [CONTRIBUTING.md](https://github.com/dispersi0no/CHAT-VLM-LLM/blob/main/CONTRIBUTING.md)")


