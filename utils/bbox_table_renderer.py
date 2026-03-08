"""
BBOX Table Renderer — compatibility re-export.
Functionality has been consolidated into utils.table_renderer.
"""

from .table_renderer import BBoxTableRenderer  # noqa: F401

__all__ = ['BBoxTableRenderer']
