"""UI components for Streamlit application."""

from .styles import get_custom_css
from .components import (
    render_metric_card,
    render_progress_bar,
    render_model_card,
    render_feature_list,
    render_code_example,
    render_comparison_table,
    render_alert,
    render_image_preview,
    render_tabs_content,
    render_download_buttons
)
from .message_renderer import (
    render_message_with_json_and_html_tables,
    is_dots_ocr_json_response,
    convert_dots_ocr_json_to_text_table,
    convert_html_table_to_text,
)
from .bbox_display import display_bbox_visualization_improved
from .sidebar import render_sidebar

__all__ = [
    'get_custom_css',
    'render_metric_card',
    'render_progress_bar',
    'render_model_card',
    'render_feature_list',
    'render_code_example',
    'render_comparison_table',
    'render_alert',
    'render_image_preview',
    'render_tabs_content',
    'render_download_buttons',
    'render_message_with_json_and_html_tables',
    'is_dots_ocr_json_response',
    'convert_dots_ocr_json_to_text_table',
    'convert_html_table_to_text',
    'display_bbox_visualization_improved',
    'render_sidebar',
]
