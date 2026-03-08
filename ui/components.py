"""Reusable UI components for Streamlit application."""

import html
from typing import Any, Dict, List

import pandas as pd
import streamlit as st


def render_metric_card(
    title: str, value: str, delta: str = None, icon: str = "📊"
) -> None:
    """
    Render a metric card with custom styling.

    Args:
        title: Metric title
        value: Metric value
        delta: Optional delta value
        icon: Optional icon emoji
    """
    _icon = html.escape(str(icon))
    _title = html.escape(str(title))
    _value = html.escape(str(value))
    _delta = html.escape(str(delta)) if delta else None
    st.markdown(
        f'<div class="info-card">'
        f"<h3>{_icon} {_title}</h3>"
        f'<h2 style="color: var(--primary-color);">{_value}</h2>'
        f'{f"<p>{_delta}</p>" if _delta else ""}'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_progress_bar(label: str, progress: float, status: str = "") -> None:
    """
    Render a progress bar with label and status.

    Args:
        label: Progress bar label
        progress: Progress value (0.0 to 1.0)
        status: Optional status text
    """
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{html.escape(str(label))}**")
        st.progress(progress)
    with col2:
        if status:
            st.markdown(
                f"<p style='text-align: right;'>{html.escape(str(status))}</p>",
                unsafe_allow_html=True,
            )


def render_model_card(model_key: str, config: Dict[str, Any]) -> None:
    """
    Render a model information card.

    Args:
        model_key: Model identifier
        config: Model configuration
    """
    _name = html.escape(str(config.get("name", "")))
    _description = html.escape(str(config.get("description", "")))
    _max_length = html.escape(str(config.get("max_length", "")))
    _precision = html.escape(str(config.get("precision", "")))
    _device_map = html.escape(str(config.get("device_map", "")))
    st.markdown(
        f'<div class="feature-card">'
        f"<h3>🤖 {_name}</h3>"
        f"<p>{_description}</p>"
        f'<ul style="text-align: left; margin-top: 1rem;">'
        f"<li>Max tokens: {_max_length}</li>"
        f"<li>Precision: {_precision}</li>"
        f"<li>Device: {_device_map}</li>"
        f"</ul>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_feature_list(features: List[str], title: str = "Features") -> None:
    """
    Render a feature list with checkmarks.

    Args:
        features: List of feature descriptions
        title: Section title
    """
    st.markdown(f"**{title}:**")
    for feature in features:
        st.markdown(f"- ✅ {feature}")


def render_code_example(
    code: str, language: str = "python", caption: str = None
) -> None:
    """
    Render a code example with optional caption.

    Args:
        code: Code to display
        language: Programming language
        caption: Optional caption
    """
    if caption:
        st.caption(caption)
    st.code(code, language=language)


def render_comparison_table(data: pd.DataFrame, title: str = "Comparison") -> None:
    """
    Render a comparison table with custom styling.

    Args:
        data: DataFrame to display
        title: Table title
    """
    st.markdown(f"### {title}")
    st.dataframe(data, use_container_width=True, hide_index=True)


def render_alert(message: str, alert_type: str = "info") -> None:
    """
    Render an alert message.

    Args:
        message: Alert message
        alert_type: Type of alert (info, success, warning, error)
    """
    alert_functions = {
        "info": st.info,
        "success": st.success,
        "warning": st.warning,
        "error": st.error,
    }

    alert_func = alert_functions.get(alert_type, st.info)
    alert_func(message)


def render_image_preview(
    image, caption: str = "Preview", max_width: int = None
) -> None:
    """
    Render an image preview with caption.

    Args:
        image: PIL Image or path
        caption: Image caption
        max_width: Optional maximum width
    """
    st.image(
        image, caption=caption, use_container_width=True if max_width is None else False
    )


def render_tabs_content(tabs_data: Dict[str, str]) -> None:
    """
    Render tabbed content.

    Args:
        tabs_data: Dictionary mapping tab names to markdown content
    """
    tabs = st.tabs(list(tabs_data.keys()))

    for tab, (tab_name, content) in zip(tabs, tabs_data.items()):
        with tab:
            st.markdown(content)


def render_download_buttons(data_dict: Dict[str, tuple]) -> None:
    """
    Render multiple download buttons in columns.

    Args:
        data_dict: Dictionary mapping button labels to (data, filename, mime) tuples
    """
    cols = st.columns(len(data_dict))

    for col, (label, (data, filename, mime)) in zip(cols, data_dict.items()):
        with col:
            st.download_button(
                label,
                data=data,
                file_name=filename,
                mime=mime,
                use_container_width=True,
            )
