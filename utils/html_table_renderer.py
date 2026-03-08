"""
HTML Table Renderer — compatibility re-export.
Functionality has been consolidated into utils.table_renderer (rendering)
and utils.table_parser (extraction).
"""

# Re-export the full renderer class so existing imports keep working.
from .table_renderer import HTMLTableRenderer  # noqa: F401

__all__ = ["HTMLTableRenderer"]
