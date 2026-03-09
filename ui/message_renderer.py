"""Message rendering functions for the Streamlit chat interface."""

from __future__ import annotations

import json
import re

import streamlit as st

from utils.constants import CATEGORY_EMOJIS


def render_message_with_json_and_html_tables(
    content: str, role: str = "assistant"
) -> None:
    """
    ОБРАБОТКА JSON И HTML ТАБЛИЦ - ТЕКСТОВАЯ ВЕРСИЯ
    Конвертирует JSON ответы dots.ocr в текстовые таблицы (БЕЗ HTML)
    """

    if role == "assistant":
        # Проверяем наличие JSON данных от dots.ocr
        if is_dots_ocr_json_response(content):
            # Конвертируем JSON в текстовую таблицу (БЕЗ HTML)
            text_table = convert_dots_ocr_json_to_text_table(content)

            # Отображаем как текстовую таблицу
            st.markdown("🔧 **JSON данные конвертированы в текстовую таблицу**")
            st.markdown(text_table)
            st.success("✅ JSON → Текст конвертация выполнена")
            return

        # Проверяем наличие готовых HTML таблиц - конвертируем в текст
        elif "<table" in content.lower() and "</table>" in content.lower():
            # Конвертируем HTML в текст
            text_content = convert_html_table_to_text(content)

            # Отображаем как текст
            st.markdown("🔧 **HTML таблица конвертирована в текст**")
            st.markdown(text_content)
            st.success("✅ HTML → Текст рендеринг")
            return

    # Обычное сообщение
    st.markdown(content)


def is_dots_ocr_json_response(content: str) -> bool:
    """Проверяет, является ли контент JSON ответом от dots.ocr"""

    # Проверяем, начинается ли строка с JSON массива
    stripped_content = content.strip()
    if stripped_content.startswith("[{") and stripped_content.endswith("}]"):
        try:
            # Пытаемся парсить как JSON
            data = json.loads(stripped_content)
            if isinstance(data, list) and len(data) > 0:
                # Проверяем, что это BBOX данные
                first_item = data[0]
                if (
                    isinstance(first_item, dict)
                    and "bbox" in first_item
                    and "category" in first_item
                ):
                    return True
        except Exception:
            pass

    return False


def convert_dots_ocr_json_to_text_table(content: str) -> str:
    """Конвертирует JSON ответ dots.ocr в текстовую таблицу (БЕЗ HTML)"""

    try:
        # Извлекаем JSON из контента
        stripped_content = content.strip()

        # Парсим JSON
        data = json.loads(stripped_content)

        if not isinstance(data, list) or len(data) == 0:
            return content

        # Заголовок
        st.markdown("📊 **Результаты анализа документа:**\n")

        # Статистика
        categories = {}
        text_elements = 0

        for item in data:
            category = item.get("category", "Unknown")
            categories[category] = categories.get(category, 0) + 1
            if item.get("text", "").strip():
                text_elements += 1

        # Отображаем статистику в колонках
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Всего элементов", len(data))
        with col2:
            st.metric("Элементов с текстом", text_elements)
        with col3:
            st.metric("Категорий", len(categories))

        # Легенда категорий с эмодзи
        st.markdown("**🎨 Категории:**")

        legend_cols = st.columns(min(len(categories), 4))
        for i, (category, count) in enumerate(sorted(categories.items())):
            col_idx = i % len(legend_cols)
            emoji = CATEGORY_EMOJIS.get(category, "📄")
            with legend_cols[col_idx]:
                st.markdown(f"{emoji} **{category}**")
                st.caption(f"Элементов: {count}")

        # Детальная информация
        st.markdown("**📋 Детальная информация:**")

        for i, item in enumerate(data, 1):
            bbox = item.get("bbox", [])
            category = item.get("category", "Unknown")
            text = item.get("text", "")

            # Форматируем BBOX координаты
            bbox_str = f"[{', '.join(map(str, bbox))}]" if bbox else "N/A"

            # Ограничиваем длину текста
            if len(text) > 50:
                text = text[:47] + "..."

            # Эмодзи для категории
            emoji = CATEGORY_EMOJIS.get(category, "📄")

            # Отображение элемента в контейнере
            with st.container():
                col_num, col_cat, col_bbox, col_text = st.columns([0.5, 1.5, 2, 4])

                with col_num:
                    st.markdown(f"**{i}**")

                with col_cat:
                    st.markdown(f"{emoji} {category}")

                with col_bbox:
                    st.code(bbox_str)

                with col_text:
                    if text:
                        st.caption(text)
                    else:
                        st.caption("_Нет текста_")

                # Разделитель между элементами
                if i < len(data):
                    st.markdown("---")

        return ""  # Возвращаем пустую строку, так как все отображено через Streamlit элементы

    except Exception as e:
        # Если не удалось конвертировать, возвращаем исходный контент
        return f"⚠️ **Не удалось конвертировать JSON:** {str(e)}\n\n```\n{content}\n```"


def convert_html_table_to_text(content: str) -> str:
    """Конвертирует HTML таблицы в текстовый формат"""

    # Извлекаем все таблицы
    table_pattern = r"<table[^>]*>(.*?)</table>"
    tables = re.findall(table_pattern, content, re.DOTALL | re.IGNORECASE)

    result_content = content

    for table_html in tables:
        try:
            # Извлекаем строки
            row_pattern = r"<tr[^>]*>(.*?)</tr>"
            rows = re.findall(row_pattern, table_html, re.DOTALL | re.IGNORECASE)

            text_rows = []

            for row in rows:
                # Извлекаем ячейки (th или td)
                cell_pattern = r"<t[hd][^>]*>(.*?)</t[hd]>"
                cells = re.findall(cell_pattern, row, re.DOTALL | re.IGNORECASE)

                if not cells:
                    continue

                # Очищаем содержимое ячеек
                clean_cells = []
                for cell in cells:
                    clean_cell = re.sub(r"<[^>]+>", "", cell)  # Убираем HTML теги
                    clean_cell = clean_cell.strip().replace("\n", " ")
                    # Ограничиваем длину
                    if len(clean_cell) > 30:
                        clean_cell = clean_cell[:27] + "..."
                    clean_cells.append(clean_cell)

                # Формируем строку
                text_row = " | ".join(clean_cells)
                text_rows.append(text_row)

            # Создаем текстовую таблицу
            text_table = "\n📊 **Таблица:**\n\n" + "\n".join(text_rows) + "\n\n"

            # Заменяем HTML таблицу на текст
            full_table_pattern = f"<table[^>]*>{re.escape(table_html)}</table>"
            result_content = re.sub(
                full_table_pattern, text_table, result_content, flags=re.IGNORECASE
            )

        except Exception:
            # Если конвертация не удалась, просто убираем HTML теги
            clean_table = re.sub(r"<[^>]+>", "", table_html)
            result_content = result_content.replace(
                f"<table>{table_html}</table>",
                f"\n\n**📊 Таблица:**\n{clean_table}\n\n",
            )

    return result_content
