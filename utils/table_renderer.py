"""
Consolidated Table Renderer Module
Объединяет логику рендеринга таблиц из:
  - bbox_table_renderer.py
  - html_table_renderer.py (части рендеринга)
  - xml_formatter.py
  - ocr_output_processor.py (export_tables_to_excel, export_to_json)
"""

import re
import json
from typing import List, Dict, Any, Optional
import pandas as pd

from .table_parser import (
    HtmlTableParser,
    XMLTableParser,
    analyze_ocr_output,
)


# ---------------------------------------------------------------------------
# BBox-based HTML table renderer (originally in bbox_table_renderer.py)
# ---------------------------------------------------------------------------

class BBoxTableRenderer:
    """Класс для создания HTML таблиц с BBOX результатами"""

    CATEGORY_COLORS = {
        'Text': '#FF6B6B',
        'Title': '#4ECDC4',
        'Table': '#45B7D1',
        'Picture': '#96CEB4',
        'Formula': '#FFEAA7',
        'Caption': '#DDA0DD',
        'Footnote': '#F0A500',
        'List-item': '#FF7675',
        'Page-header': '#74B9FF',
        'Page-footer': '#A29BFE',
        'Section-header': '#FD79A8',
        'Signature': '#00B894',
        'Stamp': '#E17055',
        'Logo': '#6C5CE7',
        'Barcode': '#FDCB6E',
        'QR-code': '#E84393'
    }

    def get_category_color(self, category: str) -> str:
        """Получение цвета для категории"""
        category_normalized = category.strip().title()
        return self.CATEGORY_COLORS.get(category_normalized, '#999999')

    def render_elements_table(self, elements: List[Dict[str, Any]]) -> str:
        """Создание HTML таблицы с элементами"""
        if not elements:
            return "<p>Нет элементов для отображения</p>"

        html = """
        <style>
            .bbox-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .bbox-table thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .bbox-table th {
                padding: 12px 15px;
                text-align: left;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 0.5px;
            }
            .bbox-table tbody tr {
                border-bottom: 1px solid #e0e0e0;
                transition: background-color 0.2s;
            }
            .bbox-table tbody tr:hover {
                background-color: #f5f5f5;
            }
            .bbox-table tbody tr:last-child {
                border-bottom: 2px solid #667eea;
            }
            .bbox-table td {
                padding: 10px 15px;
                font-size: 14px;
            }
            .category-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 11px;
                color: white;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .bbox-coords {
                font-family: 'Courier New', monospace;
                background-color: #f0f0f0;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                color: #333;
            }
            .element-text {
                max-width: 300px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                color: #555;
            }
            .element-number {
                font-weight: 700;
                color: #667eea;
                font-size: 16px;
            }
        </style>

        <table class="bbox-table">
            <thead>
                <tr>
                    <th style="width: 50px;">#</th>
                    <th style="width: 150px;">Категория</th>
                    <th style="width: 200px;">BBOX координаты</th>
                    <th>Текст</th>
                </tr>
            </thead>
            <tbody>
        """

        for i, element in enumerate(elements, 1):
            bbox = element.get('bbox', [0, 0, 0, 0])
            category = element.get('category', 'Unknown')
            text = element.get('text', '')

            color = self.get_category_color(category)
            bbox_str = f"[{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]"

            display_text = text[:100] + "..." if len(text) > 100 else text
            display_text = display_text.replace('\n', ' ').replace('\r', '')

            html += f"""
                <tr>
                    <td class="element-number">{i}</td>
                    <td>
                        <span class="category-badge" style="background-color: {color};">
                            {category}
                        </span>
                    </td>
                    <td>
                        <code class="bbox-coords">{bbox_str}</code>
                    </td>
                    <td class="element-text" title="{text}">{display_text}</td>
                </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def render_legend(self, elements: List[Dict[str, Any]]) -> str:
        """Создание HTML легенды с категориями"""
        if not elements:
            return ""

        categories: Dict[str, int] = {}
        for element in elements:
            category = element.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1

        html = """
        <style>
            .legend-container {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin: 15px 0;
                padding: 15px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 8px;
            }
            .legend-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                background: white;
                border-radius: 6px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }
            .legend-item:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .legend-color {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            .legend-label {
                font-weight: 600;
                color: #333;
                font-size: 13px;
            }
            .legend-count {
                background-color: #667eea;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 700;
            }
        </style>

        <div class="legend-container">
        """

        for category, count in sorted(categories.items()):
            color = self.get_category_color(category)
            html += f"""
                <div class="legend-item">
                    <div class="legend-color" style="background-color: {color};"></div>
                    <span class="legend-label">{category}</span>
                    <span class="legend-count">{count}</span>
                </div>
            """

        html += """
        </div>
        """

        return html

    def render_statistics(self, elements: List[Dict[str, Any]]) -> str:
        """Создание HTML блока со статистикой"""
        if not elements:
            return ""

        categories: Dict[str, int] = {}
        total_area = 0

        for element in elements:
            category = element.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1

            bbox = element.get('bbox', [0, 0, 0, 0])
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            total_area += area

        html = f"""
        <style>
            .stats-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
                transition: transform 0.2s;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }}
            .stat-value {{
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 5px;
            }}
            .stat-label {{
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                opacity: 0.9;
            }}
        </style>

        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-value">{len(elements)}</div>
                <div class="stat-label">Всего элементов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(categories)}</div>
                <div class="stat-label">Категорий</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_area:,}</div>
                <div class="stat-label">Общая площадь</div>
            </div>
        </div>
        """

        return html


# ---------------------------------------------------------------------------
# HTML table renderer (rendering parts from html_table_renderer.py)
# ---------------------------------------------------------------------------

class HTMLTableRenderer(HtmlTableParser):
    """Класс для обработки и рендеринга HTML таблиц в Streamlit"""

    def __init__(self):
        self.table_counter = 0

    def render_table_in_streamlit(self, table_html: str, title: Optional[str] = None) -> None:
        """Рендеринг HTML таблицы в Streamlit"""
        import streamlit as st

        self.table_counter += 1
        table_id = f"{id(self)}_{self.table_counter}"

        if title:
            st.subheader(title)
        else:
            st.subheader(f"📊 Таблица {self.table_counter}")

        clean_table = self.clean_html_table(table_html)
        st.markdown(clean_table, unsafe_allow_html=True)

        with st.expander(f"🔧 Опции таблицы {self.table_counter}"):
            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"📝 Показать Markdown", key=f"md_{table_id}"):
                    markdown_table = self.table_to_markdown(table_html)
                    st.code(markdown_table, language="markdown")

            with col2:
                if st.button(f"📊 Показать данные", key=f"data_{table_id}"):
                    table_data = self.extract_table_data(table_html)
                    st.json(table_data)

            st.text_area(f"HTML код таблицы {self.table_counter}:", clean_table, height=100, key=f"html_{table_id}")

    def process_dots_ocr_response(self, response_text: str) -> Dict[str, Any]:
        """Обработка ответа dots.ocr для поиска и рендеринга таблиц"""
        html_tables = self.extract_html_tables(response_text)

        result = {
            "found_tables": len(html_tables),
            "tables": [],
            "has_tables": len(html_tables) > 0
        }

        for i, table_html in enumerate(html_tables):
            table_info = {
                "index": i + 1,
                "html": table_html,
                "clean_html": self.clean_html_table(table_html),
                "markdown": self.table_to_markdown(table_html),
                "data": self.extract_table_data(table_html)
            }
            result["tables"].append(table_info)

        return result

    def render_all_tables_in_streamlit(self, response_text: str) -> None:
        """Рендеринг всех найденных таблиц в Streamlit"""
        import streamlit as st

        result = self.process_dots_ocr_response(response_text)

        if not result["has_tables"]:
            st.info("📋 В ответе не найдено HTML таблиц")
            return

        st.success(f"📊 Найдено {result['found_tables']} таблиц в ответе")

        for table_info in result["tables"]:
            self.render_table_in_streamlit(
                table_info["html"],
                f"Таблица {table_info['index']}"
            )

            if table_info["index"] < len(result["tables"]):
                st.divider()


# ---------------------------------------------------------------------------
# XML table formatter (originally in xml_formatter.py)
# ---------------------------------------------------------------------------

class XMLTableFormatter:
    """Форматировщик XML-таблиц для удобного отображения"""

    def __init__(self):
        self.parser = XMLTableParser()

    def format_table_as_text(self, table_data: Dict[str, Any],
                             separator: str = " | ",
                             show_empty: bool = False) -> str:
        """Форматирует таблицу как текст с разделителями"""
        if 'data' not in table_data:
            return ""

        lines = []
        for row in table_data['data']:
            if not show_empty:
                row = [cell for cell in row if cell.strip()]

            if row:
                lines.append(separator.join(row))

        return "\n".join(lines)

    def format_table_as_markdown(self, table_data: Dict[str, Any]) -> str:
        """Форматирует таблицу как Markdown"""
        if 'data' not in table_data:
            return ""

        data = table_data['data']
        if not data:
            return ""

        lines = []

        header = [cell if cell.strip() else "—" for cell in data[0]]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")

        for row in data[1:]:
            formatted_row = [cell if cell.strip() else "—" for cell in row]
            while len(formatted_row) < len(header):
                formatted_row.append("—")
            lines.append("| " + " | ".join(formatted_row[:len(header)]) + " |")

        return "\n".join(lines)

    def format_payment_document(self, processed_data: Dict[str, Any]) -> str:
        """Специальное форматирование для платежных документов"""
        result = []

        if 'header_info' in processed_data:
            header = processed_data['header_info']
            if 'organization' in header:
                result.append(f"Организация: {header['organization']}")
            if 'address' in header:
                result.append(f"Адрес: {header['address']}")
            if 'document_type' in header:
                result.append(f"Тип документа: {header['document_type']}")
            result.append("")

        if 'extracted_fields' in processed_data:
            fields = processed_data['extracted_fields']
            result.append("Реквизиты:")
            if 'inn' in fields:
                result.append(f"  ИНН: {fields['inn']}")
            if 'kpp' in fields:
                result.append(f"  КПП: {fields['kpp']}")
            if 'account' in fields:
                result.append(f"  Счет: {fields['account']}")
            if 'bik' in fields:
                result.append(f"  БИК: {fields['bik']}")
            if 'recipient' in fields:
                result.append(f"  Получатель: {fields['recipient']}")
            if 'bank' in fields:
                result.append(f"  Банк: {fields['bank']}")
            result.append("")

        if 'tables' in processed_data:
            for i, table in enumerate(processed_data['tables']):
                result.append(f"Таблица {i+1}:")
                result.append(self.format_table_as_text(table, show_empty=False))
                result.append("")

        return "\n".join(result)

    def extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """Извлекает пары ключ-значение из текста"""
        pairs: Dict[str, str] = {}

        patterns = [
            r'ИНН\s*:?\s*(\d+)',
            r'КПП\s*:?\s*(\d+)',
            r'БИК\s*:?\s*(\d+)',
            r'Сч\.\s*№?\s*:?\s*(\d+)',
            r'Счет\s*№?\s*:?\s*(\d+)',
            r'№\s*(\d+)',
            r'от\s+(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
        ]

        field_names = ['ИНН', 'КПП', 'БИК', 'Счет', 'Счет', 'Номер', 'Дата']

        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                field_name = field_names[i]
                if field_name not in pairs:
                    pairs[field_name] = matches[0]

        return pairs

    def format_mixed_content(self, text: str,
                             format_tables: bool = True,
                             extract_fields: bool = True) -> str:
        """Форматирует смешанный контент (текст + XML таблицы)"""
        result = []

        if '<table' in text.lower():
            analysis = analyze_ocr_output(text)

            if 'processed_data' in analysis and 'clean_text' in analysis['processed_data']:
                clean_text = analysis['processed_data']['clean_text']
                result.append("Текст документа:")
                result.append(clean_text)
                result.append("")

            if extract_fields and 'processed_data' in analysis and 'fields' in analysis['processed_data']:
                fields = analysis['processed_data']['fields']
                if fields:
                    result.append("Извлеченные данные:")
                    for key, value in fields.items():
                        result.append(f"  {key.upper()}: {value}")
                    result.append("")

            if format_tables and 'tables' in analysis:
                for i, table in enumerate(analysis['tables']):
                    result.append(f"Таблица {i+1}:")
                    result.append(self.format_table_as_text(table, show_empty=False))
                    result.append("")
        else:
            result.append(text)

            if extract_fields:
                pairs = self.extract_key_value_pairs(text)
                if pairs:
                    result.append("")
                    result.append("Извлеченные данные:")
                    for key, value in pairs.items():
                        result.append(f"  {key}: {value}")

        return "\n".join(result)


def format_ocr_result(text: str,
                      format_type: str = "mixed",
                      show_tables: bool = True,
                      show_fields: bool = True) -> str:
    """
    Быстрая функция для форматирования результата OCR

    Args:
        text: Текст от OCR
        format_type: Тип форматирования ('mixed', 'clean', 'markdown', 'payment')
        show_tables: Показывать таблицы
        show_fields: Показывать извлеченные поля

    Returns:
        Отформатированный текст
    """
    formatter = XMLTableFormatter()

    if format_type == "clean":
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text

    elif format_type == "markdown":
        if '<table' in text.lower():
            analysis = analyze_ocr_output(text)
            result = []

            if 'tables' in analysis:
                for i, table in enumerate(analysis['tables']):
                    result.append(f"## Таблица {i+1}")
                    result.append(formatter.format_table_as_markdown(table))
                    result.append("")

            return "\n".join(result)
        else:
            return text

    elif format_type == "payment":
        if '<table' in text.lower():
            analysis = analyze_ocr_output(text)
            return formatter.format_payment_document(analysis)
        else:
            return text

    else:  # mixed
        return formatter.format_mixed_content(text, show_tables, show_fields)


# ---------------------------------------------------------------------------
# Export utilities (moved from ocr_output_processor.py)
# ---------------------------------------------------------------------------

def export_tables_to_excel(processed_data: Dict[str, Any], filename: str) -> bool:
    """Экспортирует таблицы в Excel файл"""
    try:
        if 'tables' not in processed_data.get('processed_data', {}):
            return False

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for i, table in enumerate(processed_data['processed_data']['tables']):
                df = pd.DataFrame(table['data'])
                sheet_name = f'Table_{i+1}'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

        return True
    except Exception as e:
        print(f"Export error: {e}")
        return False


def export_to_json(processed_data: Dict[str, Any], filename: str) -> bool:
    """Экспортирует данные в JSON файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"JSON export error: {e}")
        return False
