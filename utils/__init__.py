"""Utility modules for image processing and text extraction."""

from .image_processor import ImageProcessor
from .text_extractor import TextExtractor
from .field_parser import FieldParser
from .markdown_renderer import MarkdownRenderer
from .logger import setup_logger, logger
from .cache import SimpleCache, cached, app_cache
from .export import export_to_json, export_to_csv, export_to_txt, create_export_package
from .validators import (
    ValidationError,
    validate_image,
    validate_model_key,
    validate_text_input,
    sanitize_filename
)
from .model_cache import (
    ModelCacheManager,
    check_model_availability,
    format_size
)
from .table_parser import (
    TableCell,
    ParsedTable,
    XMLTableParser,
    PaymentDocumentParser,
    HTMLTableParser,
    analyze_ocr_output,
)
from .table_renderer import (
    BBoxTableRenderer,
    HTMLTableRenderer,
    XMLTableFormatter,
    format_ocr_result,
    export_tables_to_excel,
    export_to_json as export_table_to_json,
)

__all__ = [
    # Image processing
    'ImageProcessor',

    # Text extraction
    'TextExtractor',

    # Field parsing
    'FieldParser',

    # Markdown rendering
    'MarkdownRenderer',

    # Logging
    'setup_logger',
    'logger',

    # Caching
    'SimpleCache',
    'cached',
    'app_cache',

    # Export
    'export_to_json',
    'export_to_csv',
    'export_to_txt',
    'create_export_package',

    # Validation
    'ValidationError',
    'validate_image',
    'validate_model_key',
    'validate_text_input',
    'sanitize_filename',

    # Model cache
    'ModelCacheManager',
    'check_model_availability',
    'format_size',

    # Table parsing
    'TableCell',
    'ParsedTable',
    'XMLTableParser',
    'PaymentDocumentParser',
    'HTMLTableParser',
    'analyze_ocr_output',

    # Table rendering
    'BBoxTableRenderer',
    'HTMLTableRenderer',
    'XMLTableFormatter',
    'format_ocr_result',
    'export_tables_to_excel',
    'export_table_to_json',
]