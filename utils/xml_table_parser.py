"""
XML Table Parser for OCR Model Output
Обработчик XML-таблиц из вывода OCR моделей

Backward-compatible wrapper — all logic now lives in table_parser.py.
"""

# Re-export everything from the consolidated module
from .table_parser import (  # noqa: F401
    TableCell,
    ParsedTable,
    XMLTableParser,
    PaymentDocumentParser,
    analyze_ocr_output,
)
