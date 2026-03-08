"""
HTML Table Renderer for dots.ocr responses
Утилита для рендеринга HTML таблиц из ответов dots.ocr

Backward-compatible wrapper — all logic now lives in
table_parser.py (parsing) and table_renderer.py (rendering).
"""

# Re-export everything from the consolidated modules
from .table_parser import HtmlTableParser  # noqa: F401
from .table_renderer import HTMLTableRenderer  # noqa: F401
