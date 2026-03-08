"""
XML Formatter — compatibility re-export.
Functionality has been consolidated into utils.table_renderer.
"""

from .table_renderer import XMLTableFormatter, format_ocr_result  # noqa: F401

__all__ = ['XMLTableFormatter', 'format_ocr_result']
