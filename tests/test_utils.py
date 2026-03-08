"""Tests for utility modules."""

import numpy as np
import pytest
from PIL import Image

from utils.field_parser import FieldParser
from utils.image_processor import ImageProcessor
from utils.markdown_renderer import MarkdownRenderer
from utils.text_extractor import TextExtractor


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    img_array = np.ones((1000, 2000, 3), dtype=np.uint8) * 255
    return Image.fromarray(img_array)


@pytest.fixture
def sample_text():
    """Sample OCR text for testing."""
    return """Invoice #12345
    Date: 2024-01-15
    Total: $150.00
    Email: test@example.com
    Phone: +1-234-567-8900
    """


class TestImageProcessor:
    """Tests for ImageProcessor class."""

    def test_preprocess_basic(self, sample_image):
        """Test basic image preprocessing."""
        processed = ImageProcessor.preprocess(sample_image)
        assert isinstance(processed, Image.Image)
        assert processed.mode == "RGB"

    def test_resize_if_needed(self, sample_image):
        """Test image resizing."""
        resized = ImageProcessor.resize_if_needed(sample_image, 1500)
        assert resized.size[0] <= 1500 or resized.size[1] <= 1500

    def test_resize_not_needed(self):
        """Test that small images are not resized."""
        small_img = Image.new("RGB", (100, 100), color="white")
        resized = ImageProcessor.resize_if_needed(small_img, 2048)
        assert resized.size == small_img.size

    def test_enhance_image(self, sample_image):
        """Test image enhancement."""
        enhanced = ImageProcessor.enhance_image(sample_image)
        assert isinstance(enhanced, Image.Image)
        assert enhanced.size == sample_image.size

    def test_get_image_info(self, sample_image):
        """Test image info extraction."""
        info = ImageProcessor.get_image_info(sample_image)
        assert "size" in info
        assert "width" in info
        assert "height" in info
        assert "megapixels" in info
        assert info["width"] == 2000
        assert info["height"] == 1000


class TestTextExtractor:
    """Tests for TextExtractor class."""

    def test_clean_text(self):
        """Test text cleaning."""
        dirty_text = "  Multiple   spaces\r\nand\r\nline breaks  "
        cleaned = TextExtractor.clean_text(dirty_text)
        assert "  " not in cleaned
        assert "\r" not in cleaned

    def test_extract_numbers(self, sample_text):
        """Test number extraction."""
        numbers = TextExtractor.extract_numbers(sample_text)
        assert len(numbers) > 0
        assert "12345" in numbers or any("12345" in n for n in numbers)

    def test_extract_dates(self, sample_text):
        """Test date extraction."""
        dates = TextExtractor.extract_dates(sample_text)
        assert len(dates) > 0
        assert any("2024" in date for date in dates)

    def test_extract_emails(self, sample_text):
        """Test email extraction."""
        emails = TextExtractor.extract_emails(sample_text)
        assert len(emails) > 0
        assert "test@example.com" in emails

    def test_extract_phone_numbers(self, sample_text):
        """Test phone number extraction."""
        phones = TextExtractor.extract_phone_numbers(sample_text)
        assert len(phones) > 0

    def test_extract_amounts(self, sample_text):
        """Test monetary amount extraction."""
        amounts = TextExtractor.extract_amounts(sample_text)
        assert len(amounts) > 0
        assert any(a["currency"] == "$" for a in amounts)

    def test_split_into_lines(self, sample_text):
        """Test line splitting."""
        lines = TextExtractor.split_into_lines(sample_text)
        assert isinstance(lines, list)
        assert len(lines) > 0
        assert all(isinstance(line, str) for line in lines)

    def test_extract_key_value_pairs(self):
        """Test key-value pair extraction."""
        text = "Name: John Doe\nAge: 30\nCity: New York"
        pairs = TextExtractor.extract_key_value_pairs(text)
        assert "Name" in pairs or "name" in pairs.get("Name", "").lower()
        assert isinstance(pairs, dict)

    def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        good_text = "This is a well formatted text with proper spacing."
        score = TextExtractor.calculate_confidence_score(good_text)
        assert 0 <= score <= 1
        assert score > 0.5  # Should have decent confidence

        bad_text = "!!!###$$$%%%^^^&&&***"
        bad_score = TextExtractor.calculate_confidence_score(bad_text)
        assert bad_score < 0.7  # Should have lower confidence


class TestFieldParser:
    """Tests for FieldParser class."""

    def test_parse_passport(self):
        """Test passport field parsing."""
        text = """Surname: DOE
        Given Names: JOHN
        Passport Number: AB123456
        Date of Birth: 01/01/1990
        """
        fields = FieldParser.parse_passport(text)
        assert isinstance(fields, dict)
        assert "surname" in fields
        assert "passport_number" in fields

    def test_parse_invoice(self):
        """Test invoice field parsing."""
        text = """Invoice Number: INV-12345
        Invoice Date: 2024-01-15
        Total Amount: $150.00
        """
        fields = FieldParser.parse_invoice(text)
        assert isinstance(fields, dict)
        assert "invoice_number" in fields
        assert "total_amount" in fields

    def test_parse_receipt(self):
        """Test receipt field parsing."""
        text = """Store Name
        Date: 2024-01-15
        Time: 14:30:00
        Total: $50.00
        """
        fields = FieldParser.parse_receipt(text)
        assert isinstance(fields, dict)
        assert "date" in fields
        assert "total" in fields

    def test_parse_custom_fields(self):
        """Test custom field parsing."""
        text = "Company: ACME Corp\nAddress: 123 Main St"
        fields = FieldParser.parse_custom_fields(text, ["Company", "Address"])
        assert "Company" in fields
        assert "Address" in fields


class TestMarkdownRenderer:
    """Tests for MarkdownRenderer class."""

    def test_format_ocr_result(self):
        """Test OCR result formatting."""
        text = "Sample OCR text"
        formatted = MarkdownRenderer.format_ocr_result(text, confidence=0.95)
        assert "###" in formatted
        assert text in formatted
        assert "95" in formatted or "0.95" in formatted

    def test_format_fields_table(self):
        """Test fields table formatting."""
        fields = {"Name": "John", "Age": "30"}
        table = MarkdownRenderer.format_fields_table(fields)
        assert "|" in table
        assert "Name" in table
        assert "John" in table

    def test_format_comparison(self):
        """Test comparison formatting."""
        results = {
            "Model A": {"accuracy": 0.95, "speed": "2s"},
            "Model B": {"accuracy": 0.92, "speed": "3s"},
        }
        formatted = MarkdownRenderer.format_comparison(results)
        assert "Model A" in formatted
        assert "Model B" in formatted
        assert "|" in formatted

    def test_create_collapsible_section(self):
        """Test collapsible section creation."""
        section = MarkdownRenderer.create_collapsible_section("Title", "Content")
        assert "<details>" in section
        assert "<summary>" in section
        assert "Title" in section
        assert "Content" in section

    def test_format_chat_message(self):
        """Test chat message formatting."""
        message = MarkdownRenderer.format_chat_message("user", "Hello")
        assert "user" in message.lower()
        assert "Hello" in message
