"""
XML Table Parser for OCR Model Output — compatibility re-export.
Functionality has been consolidated into utils.table_parser.
"""

# Re-export everything from the consolidated module so existing imports keep working.
from .table_parser import (  # noqa: F401
    TableCell,
    ParsedTable,
    XMLTableParser,
    PaymentDocumentParser,
    analyze_ocr_output,
)

__all__ = [
    'TableCell',
    'ParsedTable',
    'XMLTableParser',
    'PaymentDocumentParser',
    'analyze_ocr_output',
]
