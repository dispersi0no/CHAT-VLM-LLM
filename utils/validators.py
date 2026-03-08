"""Input validation utilities."""

import io
from typing import Optional, Tuple

from PIL import Image


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_image(
    image_bytes: bytes,
    max_size: int = 10 * 1024 * 1024,  # 10MB
    allowed_formats: Tuple[str, ...] = ("JPEG", "PNG", "BMP", "TIFF"),
) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded image.

    Args:
        image_bytes: Image file bytes
        max_size: Maximum file size in bytes
        allowed_formats: Tuple of allowed image formats

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    if len(image_bytes) > max_size:
        return False, f"Image size exceeds maximum ({max_size / 1024 / 1024:.1f}MB)"

    try:
        # Try to open image
        image = Image.open(io.BytesIO(image_bytes))

        # Check format
        if image.format not in allowed_formats:
            return (
                False,
                f"Image format '{image.format}' not supported. Allowed: {', '.join(allowed_formats)}",
            )

        # Check dimensions
        width, height = image.size
        if width < 10 or height < 10:
            return False, "Image dimensions too small (minimum 10x10 pixels)"

        if width > 10000 or height > 10000:
            return False, "Image dimensions too large (maximum 10000x10000 pixels)"

        return True, None

    except Exception as e:
        return False, f"Invalid image file: {str(e)}"


def validate_model_key(
    model_key: str, available_models: list
) -> Tuple[bool, Optional[str]]:
    """
    Validate model key.

    Args:
        model_key: Model identifier
        available_models: List of available model keys

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not model_key:
        return False, "Model key cannot be empty"

    if model_key not in available_models:
        return (
            False,
            f"Model '{model_key}' not found. Available: {', '.join(available_models)}",
        )

    return True, None


def validate_text_input(
    text: str, min_length: int = 1, max_length: int = 10000
) -> Tuple[bool, Optional[str]]:
    """
    Validate text input.

    Args:
        text: Input text
        min_length: Minimum text length
        max_length: Maximum text length

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Text cannot be empty"

    text_length = len(text)

    if text_length < min_length:
        return False, f"Text too short (minimum {min_length} characters)"

    if text_length > max_length:
        return False, f"Text too long (maximum {max_length} characters)"

    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators and dangerous characters
    dangerous_chars = ["/", "\\", "..", ":", "*", "?", '"', "<", ">", "|"]

    sanitized = filename
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "_")

    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")
        max_name_length = 250 - len(ext)
        sanitized = f"{name[:max_name_length]}.{ext}" if ext else name[:255]

    return sanitized
