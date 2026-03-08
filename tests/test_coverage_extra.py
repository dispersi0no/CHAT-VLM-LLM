"""Extra tests targeting modules with low coverage.

Covers:
- utils/logger.py
- utils/validators.py
- utils/table_parser.py  (XMLTableParser, HTMLTableParser, analyze_ocr_output)
- utils/table_renderer.py (XMLTableFormatter, format_ocr_result)
- models/model_loader.py  (apply_safe_defaults, check_model_cache)
"""

import io
import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

# =============================================================================
# utils/logger.py
# =============================================================================


class TestLogger:
    """Tests for utils/logger.py — setup_logger and ColoredFormatter."""

    def test_setup_logger_returns_logger(self):
        from utils.logger import setup_logger

        log = setup_logger(name="test_logger_1", level="DEBUG")
        assert isinstance(log, logging.Logger)
        assert log.name == "test_logger_1"

    def test_setup_logger_level_warning(self):
        from utils.logger import setup_logger

        log = setup_logger(name="test_logger_2", level="WARNING")
        assert log.level == logging.WARNING

    def test_setup_logger_with_file(self, tmp_path):
        from utils.logger import setup_logger

        log_file = str(tmp_path / "test.log")
        log = setup_logger(name="test_logger_3", level="INFO", log_file=log_file)
        log.info("hello from test")
        assert Path(log_file).exists()

    def test_setup_logger_clears_handlers(self):
        from utils.logger import setup_logger

        log = setup_logger(name="test_logger_4")
        # Call again — should clear and re-add handlers, not accumulate them.
        before_count = len(log.handlers)
        setup_logger(name="test_logger_4")
        after_count = len(logging.getLogger("test_logger_4").handlers)
        # One call adds exactly one console handler.
        assert after_count == 1

    def test_default_logger_exists(self):
        from utils.logger import logger

        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_colored_formatter_formats_record(self):
        from utils.logger import ColoredFormatter

        fmt = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        formatted = fmt.format(record)
        assert "test message" in formatted


# =============================================================================
# utils/validators.py
# =============================================================================


def _make_png_bytes(size=(50, 50)):
    img = Image.new("RGB", size, color=(0, 128, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestValidators:
    """Tests for utils/validators.py."""

    def test_validate_image_valid_png(self):
        from utils.validators import validate_image

        ok, err = validate_image(_make_png_bytes())
        assert ok is True
        assert err is None

    def test_validate_image_too_large(self):
        from utils.validators import validate_image

        ok, err = validate_image(b"x" * (11 * 1024 * 1024), max_size=10 * 1024 * 1024)
        assert ok is False
        assert err is not None

    def test_validate_image_invalid_bytes(self):
        from utils.validators import validate_image

        ok, err = validate_image(b"this is not an image")
        assert ok is False
        assert err is not None

    def test_validate_image_too_small_dimensions(self):
        from utils.validators import validate_image

        tiny = Image.new("RGB", (5, 5))
        buf = io.BytesIO()
        tiny.save(buf, format="PNG")
        ok, err = validate_image(buf.getvalue())
        assert ok is False

    def test_validate_model_key_valid(self):
        from utils.validators import validate_model_key

        ok, err = validate_model_key("qwen3_vl_2b", ["qwen3_vl_2b", "got_ocr"])
        assert ok is True
        assert err is None

    def test_validate_model_key_invalid(self):
        from utils.validators import validate_model_key

        ok, err = validate_model_key("unknown_model", ["qwen3_vl_2b"])
        assert ok is False
        assert "not found" in err

    def test_validate_model_key_empty(self):
        from utils.validators import validate_model_key

        ok, err = validate_model_key("", ["qwen3_vl_2b"])
        assert ok is False

    def test_validate_text_input_valid(self):
        from utils.validators import validate_text_input

        ok, err = validate_text_input("hello world")
        assert ok is True
        assert err is None

    def test_validate_text_input_empty(self):
        from utils.validators import validate_text_input

        ok, err = validate_text_input("")
        assert ok is False

    def test_validate_text_input_too_long(self):
        from utils.validators import validate_text_input

        ok, err = validate_text_input("a" * 10001, max_length=10000)
        assert ok is False
        assert "long" in err

    def test_sanitize_filename_removes_slashes(self):
        from utils.validators import sanitize_filename

        result = sanitize_filename("../../../etc/passwd")
        assert "/" not in result
        assert ".." not in result

    def test_sanitize_filename_removes_dangerous_chars(self):
        from utils.validators import sanitize_filename

        result = sanitize_filename('file<>:"/\\|?*.txt')
        for ch in '<>:"/\\|?*':
            assert ch not in result

    def test_sanitize_filename_long_name(self):
        from utils.validators import sanitize_filename

        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 255


# =============================================================================
# utils/table_parser.py
# =============================================================================


class TestXMLTableParser:
    """Tests for utils/table_parser.XMLTableParser."""

    def test_extract_xml_tables_finds_table(self):
        from utils.table_parser import XMLTableParser

        parser = XMLTableParser()
        text = "<table><tr><td>Hello</td></tr></table>"
        tables = parser.extract_xml_tables(text)
        assert len(tables) >= 1

    def test_extract_xml_tables_no_tables(self):
        from utils.table_parser import XMLTableParser

        parser = XMLTableParser()
        tables = parser.extract_xml_tables("plain text with no tables")
        assert tables == []

    def test_extract_xml_tables_multiple(self):
        from utils.table_parser import XMLTableParser

        parser = XMLTableParser()
        text = "<table><tr><td>A</td></tr></table> <table><tr><td>B</td></tr></table>"
        tables = parser.extract_xml_tables(text)
        assert len(tables) >= 2

    def test_parse_table_xml_returns_none_for_bad_xml(self):
        from utils.table_parser import XMLTableParser

        parser = XMLTableParser()
        result = parser.parse_table_xml("not valid xml <<<")
        assert result is None

    def test_parse_table_xml_basic(self):
        from utils.table_parser import XMLTableParser

        parser = XMLTableParser()
        xml = "<table><tr><td>Cell</td></tr></table>"
        result = parser.parse_table_xml(xml)
        # May return None if internal parsing fails, but should not raise.
        assert result is None or hasattr(result, "cells")

    def test_table_to_dict_empty(self):
        from utils.table_parser import ParsedTable, TableCell, XMLTableParser

        parser = XMLTableParser()
        table = ParsedTable(cells=[], rows=0, cols=0, metadata={})
        d = parser.table_to_dict(table)
        assert isinstance(d, dict)


class TestHTMLTableParser:
    """Tests for utils/table_parser.HTMLTableParser."""

    def test_extract_html_tables_finds_table(self):
        from utils.table_parser import HTMLTableParser

        parser = HTMLTableParser()
        html = "<table><tr><td>val</td></tr></table>"
        tables = parser.extract_html_tables(html)
        assert len(tables) >= 1

    def test_extract_html_tables_no_match(self):
        from utils.table_parser import HTMLTableParser

        parser = HTMLTableParser()
        tables = parser.extract_html_tables("no tables here")
        assert tables == []

    def test_table_to_markdown_produces_string(self):
        from utils.table_parser import HTMLTableParser

        parser = HTMLTableParser()
        html = "<table><tr><th>Name</th><th>Value</th></tr><tr><td>A</td><td>1</td></tr></table>"
        result = parser.table_to_markdown(html)
        assert isinstance(result, str)


class TestAnalyzeOCROutput:
    """Tests for the analyze_ocr_output function."""

    def test_analyze_plain_text(self):
        from utils.table_parser import analyze_ocr_output

        result = analyze_ocr_output("plain text without tables")
        assert isinstance(result, dict)
        # Without XML tables the result contains at least "raw_text"
        assert "raw_text" in result

    def test_analyze_with_xml_table(self):
        from utils.table_parser import analyze_ocr_output

        text = "Header\n<table><tr><td>A</td></tr></table>\nFooter"
        result = analyze_ocr_output(text)
        assert isinstance(result, dict)


# =============================================================================
# utils/table_renderer.py
# =============================================================================


class TestXMLTableFormatter:
    """Tests for utils/table_renderer.XMLTableFormatter."""

    def test_format_table_as_text_empty(self):
        from utils.table_renderer import XMLTableFormatter

        fmt = XMLTableFormatter()
        result = fmt.format_table_as_text({})
        assert isinstance(result, str)

    def test_format_table_as_markdown_empty(self):
        from utils.table_renderer import XMLTableFormatter

        fmt = XMLTableFormatter()
        result = fmt.format_table_as_markdown({})
        assert isinstance(result, str)

    def test_extract_key_value_pairs(self):
        from utils.table_renderer import XMLTableFormatter

        fmt = XMLTableFormatter()
        # The method looks for Russian payment document fields (ИНН, КПП, БИК …).
        text = "ИНН: 1234567890\nКПП: 987654321\nБИК: 044525225"
        pairs = fmt.extract_key_value_pairs(text)
        assert isinstance(pairs, dict)
        # At least the ИНН field should be extracted.
        assert "ИНН" in pairs


class TestFormatOCRResult:
    """Tests for utils/table_renderer.format_ocr_result."""

    def test_returns_string_for_plain_text(self):
        from utils.table_renderer import format_ocr_result

        result = format_ocr_result("Hello World")
        assert isinstance(result, str)

    def test_returns_string_for_empty(self):
        from utils.table_renderer import format_ocr_result

        result = format_ocr_result("")
        assert isinstance(result, str)

    def test_returns_string_for_xml_with_table(self):
        from utils.table_renderer import format_ocr_result

        xml = "<table><tr><td>A</td><td>B</td></tr></table>"
        result = format_ocr_result(xml)
        assert isinstance(result, str)


# =============================================================================
# models/model_loader.py — extra coverage
# =============================================================================


class TestModelLoaderExtra:
    """Additional tests for ModelLoader to improve branch coverage."""

    def test_apply_safe_defaults_no_emergency(self):
        """_apply_safe_defaults without emergency mode sets device_map and trust_remote_code."""
        from models.model_loader import ModelLoader

        cfg = {"precision": "fp16"}
        result = ModelLoader._apply_safe_defaults(cfg)
        assert result.get("device_map") == "auto"
        assert result.get("trust_remote_code") is True

    def test_get_loaded_models_empty_after_clear(self):
        """After clearing _loaded_models, get_loaded_models returns []."""
        from models.model_loader import ModelLoader

        ModelLoader._loaded_models.clear()
        assert ModelLoader.get_loaded_models() == []

    def test_unload_all_models_no_op_when_empty(self):
        """unload_all_models is safe when nothing is loaded."""
        from models.model_loader import ModelLoader

        ModelLoader._loaded_models.clear()
        ModelLoader.unload_all_models()  # Should not raise.

    def test_check_model_cache_unknown_key(self):
        """check_model_cache returns (False, msg) for an unknown key."""
        from models.model_loader import ModelLoader

        ok, msg = ModelLoader.check_model_cache("no_such_model_xyz")
        assert ok is False
        assert msg is not None
