"""ChatVLMLLM — Streamlit application entry point."""

import streamlit as st
import yaml

from ui.pages.chat import show_chat
from ui.pages.docs import show_docs
from ui.pages.home import show_home
from ui.pages.ocr import show_ocr
from ui.sidebar import render_sidebar
from ui.styles import get_custom_css

# ── Page configuration (must be first Streamlit call) ──────────────────────
st.set_page_config(
    page_title="ChatVLMLLM - Распознавание документов и чат с VLM",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS injection ───────────────────────────────────────────────────────────
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ── Session state initialisation ────────────────────────────────────────────
_defaults = {
    "messages": [],
    "current_execution_mode": "vLLM (Рекомендуется)",
    "max_tokens": 4096,
    "temperature": 0.7,
    "uploaded_image": None,
    "ocr_result": None,
    "loaded_model": None,
}
for _key, _value in _defaults.items():
    if _key not in st.session_state:
        st.session_state[_key] = _value


# ── Configuration loading ───────────────────────────────────────────────────
def load_config() -> dict:
    """Load configuration from YAML file."""
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

# ── Page header ─────────────────────────────────────────────────────────────
st.markdown(
    '<h1 class="gradient-text" style="text-align: center;">🔬 ChatVLMLLM</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="text-align: center; font-size: 1.2rem; color: #888; margin-bottom: 2rem;">'
    "Модели машинного зрения для распознавания документов и интеллектуального чата</p>",
    unsafe_allow_html=True,
)

# ── Sidebar (navigation + model settings) ───────────────────────────────────
page, execution_mode, selected_model = render_sidebar(config)

# ── Page routing ─────────────────────────────────────────────────────────────
if "🏠 Главная" in page:
    show_home(config)
elif "📄 Режим OCR" in page:
    show_ocr(config, execution_mode, selected_model)
elif "💬 Режим чата" in page:
    show_chat(config, execution_mode, selected_model)
else:
    show_docs()

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    """
<div style="text-align: center; color: #888; padding: 2rem;">
    <p><strong>ChatVLMLLM</strong> - Образовательный исследовательский проект</p>
    <p>Создано с ❤️ используя Streamlit |
    <a href="https://github.com/dispersi0no/CHAT-VLM-LLM" target="_blank" style="color: #FF4B4B;">GitHub</a> |
    Лицензия MIT</p>
    <p style="font-size: 0.9rem; margin-top: 1rem;">🔬 Исследование моделей машинного зрения для OCR документов</p>
</div>
""",
    unsafe_allow_html=True,
)
