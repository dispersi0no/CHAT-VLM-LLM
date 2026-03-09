"""Shared constants for ChatVLMLLM."""

from __future__ import annotations

from typing import Dict

CATEGORY_EMOJIS: Dict[str, str] = {
    "Picture": "🖼️",
    "Section-header": "📋",
    "Text": "📝",
    "List-item": "📌",
    "Table": "📊",
    "Title": "🏷️",
    "Formula": "🧮",
    "Caption": "💬",
    "Footnote": "📄",
    "Page-header": "📑",
    "Page-footer": "📄",
    "Signature": "✍️",
    "Stamp": "🔖",
    "Logo": "🏢",
    "Barcode": "📊",
    "QR-code": "📱",
}

DEBUG_MODE: bool = False  # Set to True to show debug expanders
