"""Table Parser — extraction and parsing of XML/HTML tables from OCR output.

Consolidates xml_table_parser.py and the extraction part of html_table_renderer.py.
"""

import re
import html as html_module
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import json
from dataclasses import dataclass


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class TableCell:
    """Ячейка таблицы"""
    content: str
    row: int
    col: int
    colspan: int = 1
    rowspan: int = 1


@dataclass
class ParsedTable:
    """Распарсенная таблица"""
    cells: List[TableCell]
    rows: int
    cols: int
    metadata: Dict[str, Any]


# ─── XML Table Parser ─────────────────────────────────────────────────────────

class XMLTableParser:
    """Парсер XML-таблиц из вывода OCR"""

    def __init__(self):
        self.table_patterns = [
            r'<table[^>]*>(.*?)</table>',
            r'<TABLE[^>]*>(.*?)</TABLE>'
        ]

    def extract_xml_tables(self, text: str) -> List[str]:
        """Извлекает XML-таблицы из текста"""
        tables = []
        for pattern in self.table_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                full_table = f"<table>{match}</table>"
                tables.append(full_table)
        return tables

    def parse_table_xml(self, xml_content: str) -> Optional[ParsedTable]:
        """Парсит XML-таблицу в структурированный формат"""
        try:
            xml_content = self._clean_xml(xml_content)
            root = ET.fromstring(xml_content)

            cells = []
            max_row = 0
            max_col = 0

            for row_idx, tr in enumerate(root.findall('.//tr')):
                for col_idx, td in enumerate(tr.findall('.//td')):
                    content = self._extract_cell_content(td)
                    colspan = int(td.get('colspan', 1))
                    rowspan = int(td.get('rowspan', 1))

                    cell = TableCell(
                        content=content,
                        row=row_idx,
                        col=col_idx,
                        colspan=colspan,
                        rowspan=rowspan
                    )
                    cells.append(cell)
                    max_row = max(max_row, row_idx)
                    max_col = max(max_col, col_idx)

            return ParsedTable(
                cells=cells,
                rows=max_row + 1,
                cols=max_col + 1,
                metadata={}
            )

        except ET.ParseError as e:
            print(f"XML Parse Error: {e}")
            return None
        except Exception as e:
            print(f"Table parsing error: {e}")
            return None

    def _clean_xml(self, xml_content: str) -> str:
        """Очищает и исправляет XML"""
        xml_content = re.sub(r'\s+', ' ', xml_content.strip())
        xml_content = re.sub(r'<td([^>]*)>([^<]*?)(?=<td|</tr|</table|$)', r'<td\1>\2</td>', xml_content)
        xml_content = re.sub(r'<tr([^>]*)>([^<]*?)(?=<tr|</table|$)', r'<tr\1>\2</tr>', xml_content)
        if not xml_content.startswith('<table'):
            xml_content = f"<table>{xml_content}</table>"
        return xml_content

    def _extract_cell_content(self, td_element) -> str:
        """Извлекает содержимое ячейки"""
        content = td_element.text.strip() if td_element.text else ""
        for child in td_element:
            if child.text:
                content += child.text.strip()
            if child.tail:
                content += child.tail.strip()
        return content

    def table_to_dataframe(self, parsed_table: ParsedTable) -> pd.DataFrame:
        """Конвертирует таблицу в pandas DataFrame"""
        data_matrix = [["" for _ in range(parsed_table.cols)] for _ in range(parsed_table.rows)]
        for cell in parsed_table.cells:
            for r in range(cell.rowspan):
                for c in range(cell.colspan):
                    row_idx = cell.row + r
                    col_idx = cell.col + c
                    if row_idx < parsed_table.rows and col_idx < parsed_table.cols:
                        data_matrix[row_idx][col_idx] = cell.content
        return pd.DataFrame(data_matrix)

    def table_to_dict(self, parsed_table: ParsedTable) -> Dict[str, Any]:
        """Конвертирует таблицу в словарь"""
        result: Dict[str, Any] = {
            "rows": parsed_table.rows,
            "cols": parsed_table.cols,
            "cells": [],
            "data": []
        }
        for cell in parsed_table.cells:
            result["cells"].append({
                "content": cell.content,
                "row": cell.row,
                "col": cell.col,
                "colspan": cell.colspan,
                "rowspan": cell.rowspan
            })

        data_matrix = [["" for _ in range(parsed_table.cols)] for _ in range(parsed_table.rows)]
        for cell in parsed_table.cells:
            for r in range(cell.rowspan):
                for c in range(cell.colspan):
                    row_idx = cell.row + r
                    col_idx = cell.col + c
                    if row_idx < parsed_table.rows and col_idx < parsed_table.cols:
                        data_matrix[row_idx][col_idx] = cell.content
        result["data"] = data_matrix
        return result


# ─── Payment Document Parser ──────────────────────────────────────────────────

class PaymentDocumentParser(XMLTableParser):
    """Специализированный парсер для платежных документов"""

    def __init__(self):
        super().__init__()
        self.payment_fields = {
            'inn': r'ИНН\s*(\d+)',
            'kpp': r'КПП\s*(\d+)',
            'account': r'(?:Сч\.|Счет)\s*№?\s*(\d+)',
            'bik': r'БИК\s*(\d+)',
            'recipient': r'Получатель[:\s]*([^<\n]+)',
            'bank': r'Банк\s+получателя[:\s]*([^<\n]+)'
        }

    def parse_payment_document(self, text: str) -> Dict[str, Any]:
        """Парсит платежный документ"""
        result: Dict[str, Any] = {
            'header_info': self._extract_header_info(text),
            'tables': [],
            'extracted_fields': self._extract_payment_fields(text)
        }
        for xml_table in self.extract_xml_tables(text):
            parsed_table = self.parse_table_xml(xml_table)
            if parsed_table:
                result['tables'].append(self.table_to_dict(parsed_table))
        return result

    def _extract_header_info(self, text: str) -> Dict[str, str]:
        """Извлекает информацию из заголовка документа"""
        header_info: Dict[str, str] = {}
        org_match = re.search(r'ООО\s+[«"]([^»"]+)[»"]', text)
        if org_match:
            header_info['organization'] = org_match.group(0)
        address_match = re.search(r'Адрес:\s*([^<\n]+)', text)
        if address_match:
            header_info['address'] = address_match.group(1).strip()
        doc_type_match = re.search(r'(Образец\s+заполнения\s+[^<\n]+)', text)
        if doc_type_match:
            header_info['document_type'] = doc_type_match.group(1).strip()
        return header_info

    def _extract_payment_fields(self, text: str) -> Dict[str, str]:
        """Извлекает платежные реквизиты"""
        fields: Dict[str, str] = {}
        for field_name, pattern in self.payment_fields.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields[field_name] = match.group(1).strip()
        return fields


# ─── HTML Table Parser (extraction only) ─────────────────────────────────────

class HTMLTableParser:
    """Извлечение и парсинг HTML-таблиц (extraction-only, без рендеринга)"""

    def extract_html_tables(self, text: str) -> List[str]:
        """Извлечение HTML таблиц из текста"""
        table_patterns = [
            r'<table[^>]*>.*?</table>',
            r'<table>.*?</table>',
        ]
        tables: List[str] = []
        for pattern in table_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            tables.extend(matches)
        # Удаление дубликатов
        unique_tables: List[str] = []
        for table in tables:
            if table not in unique_tables:
                unique_tables.append(table)
        return unique_tables

    def table_to_markdown(self, table_html: str) -> str:
        """Конвертация HTML таблицы в Markdown"""
        try:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
            if not rows:
                return "Не удалось извлечь строки таблицы"

            markdown_rows = []
            is_header = True

            for row in rows:
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL | re.IGNORECASE)
                if not cells:
                    continue
                clean_cells = []
                for cell in cells:
                    clean_cell = re.sub(r'<[^>]+>', '', cell)
                    clean_cell = html_module.unescape(clean_cell).strip()
                    clean_cells.append(clean_cell)
                markdown_row = "| " + " | ".join(clean_cells) + " |"
                markdown_rows.append(markdown_row)
                if is_header and len(clean_cells) > 0:
                    separator = "| " + " | ".join(["---"] * len(clean_cells)) + " |"
                    markdown_rows.append(separator)
                    is_header = False

            return "\n".join(markdown_rows)
        except Exception as e:
            return f"Ошибка конвертации таблицы: {str(e)}"

    def extract_table_data(self, table_html: str) -> Dict[str, Any]:
        """Извлечение структурированных данных из HTML таблицы"""
        try:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
            if not rows:
                return {"error": "Не найдено строк в таблице"}

            table_data: Dict[str, Any] = {
                "headers": [],
                "rows": [],
                "total_rows": len(rows),
                "total_columns": 0
            }

            for i, row in enumerate(rows):
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL | re.IGNORECASE)
                if not cells:
                    continue
                clean_cells = []
                for cell in cells:
                    clean_cell = re.sub(r'<[^>]+>', '', cell)
                    clean_cell = html_module.unescape(clean_cell).strip()
                    clean_cells.append(clean_cell)
                if i == 0:
                    table_data["headers"] = clean_cells
                    table_data["total_columns"] = len(clean_cells)
                else:
                    table_data["rows"].append(clean_cells)

            return table_data
        except Exception as e:
            return {"error": f"Ошибка извлечения данных: {str(e)}"}


# ─── Top-level helper ─────────────────────────────────────────────────────────

def analyze_ocr_output(text: str, output_format: str = 'dict') -> Union[Dict[str, Any], str, 'pd.DataFrame']:
    """
    Анализирует вывод OCR модели и обрабатывает XML-таблицы

    Args:
        text: Текст вывода OCR модели
        output_format: Формат вывода ('dict', 'json', 'dataframe')

    Returns:
        Структурированные данные
    """
    if 'платежн' in text.lower() or 'получатель' in text.lower():
        pay_parser = PaymentDocumentParser()
        result = pay_parser.parse_payment_document(text)
    else:
        parser = XMLTableParser()
        result = {'tables': [], 'raw_text': text}
        for xml_table in parser.extract_xml_tables(text):
            parsed_table = parser.parse_table_xml(xml_table)
            if parsed_table:
                result['tables'].append(parser.table_to_dict(parsed_table))

    if output_format == 'json':
        return json.dumps(result, ensure_ascii=False, indent=2)
    elif output_format == 'dataframe' and result.get('tables'):
        xml_parser = XMLTableParser()
        first_table = result['tables'][0]
        cells = [TableCell(
            content=cell['content'],
            row=cell['row'],
            col=cell['col'],
            colspan=cell['colspan'],
            rowspan=cell['rowspan']
        ) for cell in first_table['cells']]
        parsed = ParsedTable(
            cells=cells,
            rows=first_table['rows'],
            cols=first_table['cols'],
            metadata={}
        )
        return xml_parser.table_to_dataframe(parsed)

    return result
