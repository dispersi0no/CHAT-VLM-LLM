"""
Утилиты для форматирования XML-таблиц в читаемый вид

Backward-compatible wrapper — all logic now lives in table_renderer.py.
"""

# Re-export from the consolidated module
from .table_renderer import (  # noqa: F401
    XMLTableFormatter,
    format_ocr_result,
)
