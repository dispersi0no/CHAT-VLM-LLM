"""
OCR Output Processor with XML Table Support
Обработчик вывода OCR с поддержкой XML-таблиц

Backward-compatible wrapper. Unique export functions have been moved to
table_renderer.py; the OCROutputProcessor class is kept here for
backward compatibility.
"""

import re
import json
from typing import Dict, Any, List, Optional, Union
from .table_parser import analyze_ocr_output, XMLTableParser, PaymentDocumentParser
from .table_renderer import (  # noqa: F401
    export_tables_to_excel,
    export_to_json as export_tables_to_json,
)
import pandas as pd


class OCROutputProcessor:
    """Процессор для обработки вывода OCR моделей"""

    def __init__(self):
        self.xml_parser = XMLTableParser()
        self.payment_parser = PaymentDocumentParser()

        self.document_patterns = {
            'payment': [
                r'платежн',
                r'получатель',
                r'банк\s+получателя',
                r'инн\s*\d+',
                r'кпп\s*\d+',
                r'бик\s*\d+'
            ],
            'invoice': [
                r'счет[^а-я]*фактур',
                r'накладн',
                r'поставщик',
                r'покупатель',
                r'сумма\s+без\s+ндс'
            ],
            'passport': [
                r'паспорт',
                r'серия\s+номер',
                r'выдан',
                r'код\s+подразделения'
            ],
            'contract': [
                r'договор',
                r'контракт',
                r'соглашение',
                r'стороны\s+договора'
            ]
        }

    def process_ocr_output(self,
                           text: str,
                           model_name: str = "unknown",
                           extract_tables: bool = True,
                           extract_fields: bool = True,
                           output_format: str = 'structured') -> Dict[str, Any]:
        """
        Обрабатывает вывод OCR модели

        Args:
            text: Текст от OCR модели
            model_name: Название модели
            extract_tables: Извлекать ли таблицы
            extract_fields: Извлекать ли поля
            output_format: Формат вывода ('structured', 'json', 'simple')

        Returns:
            Обработанные данные
        """
        result = {
            'model_name': model_name,
            'document_type': self._detect_document_type(text),
            'has_xml_tables': self._has_xml_tables(text),
            'raw_text': text,
            'processed_data': {}
        }

        if extract_tables and result['has_xml_tables']:
            table_data = self._process_xml_tables(text)
            result['processed_data']['tables'] = table_data

        if extract_fields:
            fields = self._extract_structured_fields(text, result['document_type'])
            result['processed_data']['fields'] = fields

        result['processed_data']['clean_text'] = self._clean_text(text)

        if output_format == 'json':
            return json.dumps(result, ensure_ascii=False, indent=2)
        elif output_format == 'simple':
            return self._simplify_output(result)

        return result

    def _detect_document_type(self, text: str) -> str:
        """Определяет тип документа"""
        text_lower = text.lower()

        for doc_type, patterns in self.document_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return doc_type

        return 'unknown'

    def _has_xml_tables(self, text: str) -> bool:
        """Проверяет наличие XML-таблиц в тексте"""
        xml_tables = self.xml_parser.extract_xml_tables(text)
        return len(xml_tables) > 0

    def _process_xml_tables(self, text: str) -> List[Dict[str, Any]]:
        """Обрабатывает XML-таблицы"""
        tables_data = []
        xml_tables = self.xml_parser.extract_xml_tables(text)

        for i, xml_table in enumerate(xml_tables):
            parsed_table = self.xml_parser.parse_table_xml(xml_table)
            if parsed_table:
                table_dict = self.xml_parser.table_to_dict(parsed_table)
                table_dict['table_id'] = i
                table_dict['xml_source'] = xml_table
                table_dict['analysis'] = self._analyze_table_content(table_dict)
                tables_data.append(table_dict)

        return tables_data

    def _analyze_table_content(self, table_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Анализирует содержимое таблицы"""
        analysis: Dict[str, Any] = {
            'has_numbers': False,
            'has_dates': False,
            'has_currency': False,
            'empty_cells': 0,
            'total_cells': 0,
            'key_fields': []
        }

        number_pattern = r'\d+'
        date_pattern = r'\d{1,2}[./]\d{1,2}[./]\d{2,4}'
        currency_pattern = r'\d+[.,]\d{2}\s*(?:руб|₽|$|€)'

        for row in table_dict['data']:
            for cell in row:
                analysis['total_cells'] += 1

                if not cell.strip():
                    analysis['empty_cells'] += 1
                    continue

                cell_lower = cell.lower()

                if re.search(number_pattern, cell):
                    analysis['has_numbers'] = True

                if re.search(date_pattern, cell):
                    analysis['has_dates'] = True

                if re.search(currency_pattern, cell):
                    analysis['has_currency'] = True

                key_fields = ['инн', 'кпп', 'бик', 'счет', 'сумма', 'дата']
                for field in key_fields:
                    if field in cell_lower and field not in analysis['key_fields']:
                        analysis['key_fields'].append(field)

        if analysis['total_cells'] > 0:
            analysis['fill_rate'] = (
                (analysis['total_cells'] - analysis['empty_cells']) / analysis['total_cells']
            )
        else:
            analysis['fill_rate'] = 0

        return analysis

    def _extract_structured_fields(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Извлекает структурированные поля в зависимости от типа документа"""
        if doc_type == 'payment':
            return self.payment_parser._extract_payment_fields(text)

        general_fields: Dict[str, Any] = {}

        date_pattern = r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})'
        dates = re.findall(date_pattern, text)
        if dates:
            general_fields['dates'] = dates

        number_pattern = r'№\s*(\d+(?:[/-]\d+)*)'
        numbers = re.findall(number_pattern, text)
        if numbers:
            general_fields['numbers'] = numbers

        amount_pattern = r'(\d+[.,]\d{2})\s*(?:руб|₽)'
        amounts = re.findall(amount_pattern, text)
        if amounts:
            general_fields['amounts'] = amounts

        return general_fields

    def _clean_text(self, text: str) -> str:
        """Очищает текст от XML и лишних символов"""
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = clean_text.strip()
        return clean_text

    def _simplify_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Упрощает вывод для базового использования"""
        simplified: Dict[str, Any] = {
            'document_type': result['document_type'],
            'text': result['processed_data']['clean_text']
        }

        if 'tables' in result['processed_data']:
            simplified['tables'] = []
            for table in result['processed_data']['tables']:
                simplified_table = {
                    'rows': table['rows'],
                    'cols': table['cols'],
                    'data': table['data']
                }
                simplified['tables'].append(simplified_table)

        if 'fields' in result['processed_data']:
            simplified['fields'] = result['processed_data']['fields']

        return simplified

    # Kept for backward compatibility — now delegates to table_renderer.py
    def export_tables_to_excel(self,
                               processed_data: Dict[str, Any],
                               filename: str) -> bool:
        """Экспортирует таблицы в Excel файл"""
        return export_tables_to_excel(processed_data, filename)

    def export_to_json(self,
                       processed_data: Dict[str, Any],
                       filename: str) -> bool:
        """Экспортирует данные в JSON файл"""
        return export_tables_to_json(processed_data, filename)


def process_ocr_text(text: str,
                     model_name: str = "unknown",
                     output_format: str = 'structured') -> Union[Dict[str, Any], str]:
    """
    Быстрая обработка текста OCR

    Args:
        text: Текст от OCR
        model_name: Название модели
        output_format: Формат вывода

    Returns:
        Обработанные данные
    """
    processor = OCROutputProcessor()
    return processor.process_ocr_output(text, model_name, output_format=output_format)
