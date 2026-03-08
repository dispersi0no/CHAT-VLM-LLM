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
    HtmlTableParser,
    analyze_ocr_output,
)
from .table_renderer import (
    BBoxTableRenderer,
    HTMLTableRenderer,
    XMLTableFormatter,
    format_ocr_result,
    export_tables_to_excel,
    export_to_json as export_tables_to_json,
)
from .dots_prompts import dict_promptmode_to_prompt, layout_all, prompt_layout_all_en
from .ocr_output_processor import OCROutputProcessor, process_ocr_text
from .smart_content_renderer import SmartContentRenderer

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

    # Table parsing (table_parser.py)
    'TableCell',
    'ParsedTable',
    'XMLTableParser',
    'PaymentDocumentParser',
    'HtmlTableParser',
    'analyze_ocr_output',

    # Table rendering (table_renderer.py)
    'BBoxTableRenderer',
    'HTMLTableRenderer',
    'XMLTableFormatter',
    'format_ocr_result',
    'export_tables_to_excel',
    'export_tables_to_json',

    # Prompts
    'dict_promptmode_to_prompt',
    'layout_all',
    'prompt_layout_all_en',

    # OCR output processor
    'OCROutputProcessor',
    'process_ocr_text',

    # Smart content renderer
    'SmartContentRenderer',
]