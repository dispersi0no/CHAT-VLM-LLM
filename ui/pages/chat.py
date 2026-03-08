"""Chat page for ChatVLMLLM Streamlit application."""

import gc
import re
import time

import streamlit as st
from PIL import Image

from ui.bbox_display import display_bbox_visualization_improved
from ui.message_renderer import render_message_with_json_and_html_tables

# ---------------------------------------------------------------------------
# Helper functions — shared processing logic (eliminates 3x duplication)
# ---------------------------------------------------------------------------


def _cleanup_gpu():
    """Clean GPU memory and run garbage collection."""
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    except Exception:
        pass
    gc.collect()


def _get_vllm_adapter():
    """Get or create the vLLM adapter singleton in session state."""
    from vllm_streamlit_adapter import VLLMStreamlitAdapter

    if "vllm_adapter" not in st.session_state:
        st.session_state.vllm_adapter = VLLMStreamlitAdapter()
    return st.session_state.vllm_adapter


def _safe_max_tokens(adapter, model_path: str, requested: int) -> int:
    """Compute safe max_tokens, reserving space for input tokens."""
    model_max = adapter.get_model_max_tokens(model_path)
    safe = min(requested, model_max - 500)
    return safe if safe >= 100 else model_max // 2


def _resolve_vllm_model(adapter, selected_model: str):
    """Return the vLLM model_path for the current selection, or None."""
    if "dots" in selected_model.lower():
        return "rednote-hilab/dots.ocr"
    active_key = adapter.container_manager.get_active_model()
    if active_key:
        return adapter.container_manager.models_config[active_key]["model_path"]
    return None


def _adapt_dots_response(prompt: str, ocr_text: str) -> str:
    """Adapt raw dots.ocr output based on the user's question type."""
    pl = prompt.lower()

    if any(
        w in pl
        for w in (
            "текст",
            "прочитай",
            "извлеки",
            "распознай",
            "text",
            "extract",
            "read",
        )
    ):
        return ocr_text

    if any(
        w in pl
        for w in (
            "что",
            "какой",
            "сколько",
            "есть ли",
            "найди",
            "what",
            "how",
            "is there",
            "find",
        )
    ):
        if "число" in pl or "number" in pl:
            nums = re.findall(r"\d+", ocr_text)
            return (
                f"В изображении найдены числа: {', '.join(nums)}"
                if nums
                else "В изображении не найдено чисел."
            )
        if "цвет" in pl or "color" in pl:
            return (
                "dots.ocr специализирована на распознавании текста, "
                "а не анализе цветов. Для анализа изображений "
                "используйте Qwen3-VL."
            )
        if "сколько" in pl or "how many" in pl:
            return f"В тексте примерно {len(ocr_text.split())} слов."
        if "есть ли" in pl or "is there" in pl:
            if "текст" in pl or "text" in pl:
                return f"Да, в изображении есть текст:\n\n{ocr_text}"
            return (
                "dots.ocr может определить только наличие текста. "
                f"Найденный текст:\n\n{ocr_text}"
            )
        return (
            "dots.ocr специализирована на OCR. Вот распознанный текст, "
            "который может помочь ответить на ваш вопрос:\n\n"
            f"{ocr_text}\n\n"
            "💡 Для детального анализа изображений используйте "
            "Qwen3-VL в настройках модели."
        )

    return (
        "dots.ocr специализирована на распознавании текста. "
        f"Извлеченный текст:\n\n{ocr_text}\n\n"
        "💡 Для чата об изображениях выберите Qwen3-VL "
        "в настройках модели."
    )


def _process_via_transformers(
    image,
    prompt: str,
    selected_model: str,
    max_tokens: int,
    temperature: float,
    start_time: float,
) -> str:
    """Run inference through Transformers and return the response string."""
    from models.model_loader import ModelLoader

    model = ModelLoader.load_model(selected_model)

    if hasattr(model, "chat"):
        resp = model.chat(
            image=image,
            prompt=prompt,
            temperature=temperature,
            max_new_tokens=max_tokens,
        )
    elif hasattr(model, "process_image"):
        if any(w in prompt.lower() for w in ("текст", "прочитай", "извлеки")):
            resp = model.process_image(image)
        else:
            resp = f"Это OCR модель. Извлеченный текст:\n\n{model.process_image(image)}"
    else:
        resp = "Модель не поддерживает чат. Попробуйте режим OCR."

    elapsed = time.time() - start_time
    return f"{resp}\n\n*🔧 Обработано локально за {elapsed:.2f}с с помощью {selected_model}*"


def _handle_error(error) -> str:
    """Return a user-friendly error string and show UI warnings."""
    msg = str(error)
    if "CUDA error" in msg or "device-side assert" in msg:
        st.error(
            "❌ Ошибка GPU. Попробуйте перезагрузить страницу "
            "или выбрать другую модель."
        )
        st.info(
            "💡 Рекомендация: Используйте vLLM режим " "для более стабильной работы."
        )
        return (
            "❌ Критическая ошибка GPU. Перезагрузите страницу "
            "и попробуйте vLLM режим."
        )
    if "video_processor" in msg or "NoneType" in msg:
        st.error("❌ Ошибка загрузки dots.ocr. " "Попробуйте использовать Qwen3-VL.")
        return (
            "❌ Ошибка загрузки модели dots.ocr. "
            "Используйте Qwen3-VL для аналогичных задач."
        )
    return (
        f"❌ Ошибка при обработке: {msg}\n\n"
        "💡 Попробуйте выбрать другую модель или проверьте, "
        "что модель загружена корректно."
    )


def _is_critical_error(error) -> bool:
    """Check if the error is a critical GPU error that prevents fallback."""
    msg = str(error)
    return "CUDA error" in msg or "device-side assert" in msg


def process_prompt(image, prompt: str, execution_mode: str, selected_model: str) -> str:
    """
    Unified prompt processing pipeline.

    Handles GPU cleanup, vLLM / Transformers routing, dots.ocr adaptation,
    and automatic fallback.
    """
    _cleanup_gpu()
    start_time = time.time()
    max_tokens = st.session_state.get("max_tokens", 4096)
    temperature = st.session_state.get("temperature", 0.7)

    try:
        if "vLLM" in execution_mode:
            adapter = _get_vllm_adapter()
            try:
                vllm_model = _resolve_vllm_model(adapter, selected_model)
                if vllm_model is None:
                    st.error("❌ Нет активной модели")
                    return "❌ Нет активной модели"

                safe = _safe_max_tokens(adapter, vllm_model, max_tokens)
                result = adapter.process_image(image, prompt, vllm_model, safe)

                if not result or not result["success"]:
                    return "❌ Ошибка обработки через vLLM"

                pt = result["processing_time"]
                if "dots" in selected_model.lower():
                    resp = _adapt_dots_response(prompt, result["text"])
                else:
                    resp = result["text"]
                return f"{resp}\n\n*🚀 Обработано через vLLM за {pt:.2f}с*"

            except Exception as vllm_err:
                st.error(f"❌ Ошибка vLLM режима: {vllm_err}")
                if _is_critical_error(vllm_err):
                    return _handle_error(vllm_err)
                st.info("💡 Переключаемся на Transformers режим...")
                try:
                    return _process_via_transformers(
                        image,
                        prompt,
                        selected_model,
                        max_tokens,
                        temperature,
                        start_time,
                    )
                except Exception as fb:
                    return f"❌ Ошибка и в fallback режиме: {str(fb)}"
        else:
            return _process_via_transformers(
                image, prompt, selected_model, max_tokens, temperature, start_time
            )
    except Exception as e:
        return _handle_error(e)


def process_official_prompt(
    image, prompt: str, execution_mode: str, selected_model: str
) -> str:
    """Process an official dots.ocr prompt (with model unload + Qwen3-VL fallback)."""
    _cleanup_gpu()
    try:
        from models.model_loader import ModelLoader

        ModelLoader.unload_all_models()
    except Exception:
        pass

    start_time = time.time()
    max_tokens = st.session_state.get("max_tokens", 4096)

    try:
        if "vLLM" in execution_mode:
            adapter = _get_vllm_adapter()
            model_max = adapter.get_model_max_tokens("rednote-hilab/dots.ocr")
            safe = _safe_max_tokens(adapter, "rednote-hilab/dots.ocr", max_tokens)
            st.info(
                f"🎯 Используем {safe} токенов для официального "
                f"промпта (лимит модели: {model_max})"
            )

            try:
                result = adapter.process_image(
                    image, prompt, "rednote-hilab/dots.ocr", safe
                )
            except Exception as dots_err:
                st.warning(f"⚠️ Ошибка dots.ocr: {dots_err}")
                st.info("🔄 Переключаемся на Qwen3-VL для обработки...")
                try:
                    result = adapter.process_image(
                        image, prompt, "Qwen/Qwen3-VL-2B-Instruct", max_tokens
                    )
                    if result and result["success"]:
                        result[
                            "text"
                        ] += "\n\n*⚠️ Обработано через Qwen3-VL (fallback)*"
                except Exception:
                    result = {"success": False, "text": "Ошибка обработки"}

            if result and result["success"]:
                pt = result["processing_time"]
                return (
                    f"{result['text']}\n\n"
                    f"*🎯 Официальный промпт dots.ocr обработан за {pt:.2f}с*"
                )
            return "❌ Ошибка обработки официального промпта"
        else:
            return _process_via_transformers(
                image, prompt, selected_model, max_tokens, 0.7, start_time
            )
    except Exception as e:
        return _handle_error(e)


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------

# Official dots.ocr prompt definitions
_OFFICIAL_PROMPTS = {
    "🔍 Полный анализ с BBOX": {
        "prompt": (
            "Please output the layout information from the PDF image, "
            "including each layout element's bbox, its category, and the "
            "corresponding text content within the bbox.\n\n"
            "1. Bbox format: [x1, y1, x2, y2]\n\n"
            "2. Layout Categories: The possible categories are "
            "['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', "
            "'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title'].\n\n"
            "3. Text Extraction & Formatting Rules:\n"
            "- Picture: For the 'Picture' category, the text field should be omitted.\n"
            "- Formula: Format its text as LaTeX.\n"
            "- Table: Format its text as HTML.\n"
            "- All Others (Text, Title, etc.): Format their text as Markdown.\n\n"
            "4. Constraints:\n"
            "- The output text must be the original text from the image, with no translation.\n"
            "- All layout elements must be sorted according to human reading order.\n\n"
            "5. Final Output: The entire output must be a single JSON object."
        ),
        "description": "Полный анализ документа с BBOX координатами всех элементов",
        "bbox_enabled": True,
    },
    "🖼️ Обнаружение изображений": {
        "prompt": (
            "Analyze this document image and detect all visual elements "
            "including pictures, logos, stamps, signatures, and other graphical "
            "content. For each detected element, provide:\n\n"
            "1. Bbox coordinates in format [x1, y1, x2, y2]\n"
            "2. Category (Picture, Logo, Stamp, Signature, Barcode, QR-code, etc.)\n"
            "3. Brief description of the visual element\n\n"
            "Output as JSON array with detected visual elements."
        ),
        "description": "Специализированное обнаружение графических элементов",
        "bbox_enabled": True,
    },
    "📊 Структурированные таблицы": {
        "prompt": (
            "Extract and format all table content from this document as "
            "structured HTML tables with proper formatting. Include:\n\n"
            "1. All table data with correct row and column structure\n"
            "2. Preserve headers and data relationships\n"
            "3. Format as clean HTML tables\n"
            "4. Include bbox coordinates for each table: [x1, y1, x2, y2]\n\n"
            "Output format: JSON with tables array containing bbox and "
            "html_content for each table."
        ),
        "description": "Извлечение таблиц с HTML форматированием и BBOX",
        "bbox_enabled": True,
        "table_processing": True,
    },
    "📐 Только обнаружение (BBOX)": {
        "prompt": (
            "Perform layout detection only. Identify and locate all layout "
            "elements in the document without text recognition. For each "
            "element provide:\n\n"
            "1. Bbox coordinates: [x1, y1, x2, y2]\n"
            "2. Category from: ['Caption', 'Footnote', 'Formula', 'List-item', "
            "'Page-footer', 'Page-header', 'Picture', 'Section-header', "
            "'Table', 'Text', 'Title']\n"
            "3. Confidence score if available\n\n"
            "Output as JSON array of detected layout elements."
        ),
        "description": "Только обнаружение элементов без распознавания текста",
        "bbox_enabled": True,
    },
    "🔤 Простое OCR": {
        "prompt": "Extract all text from this image.",
        "description": "Быстрое извлечение всего текста",
        "bbox_enabled": False,
    },
    "📋 Чтение по порядку": {
        "prompt": (
            "Extract all text content from this image while maintaining "
            "reading order. Exclude headers and footers."
        ),
        "description": "Извлечение текста с сохранением порядка чтения",
        "bbox_enabled": False,
    },
}

_CHAT_EXAMPLES = [
    "🔍 Что изображено на картинке?",
    "📝 Опиши содержимое документа",
    "🔢 Найди все числа в изображении",
    "📊 Есть ли таблицы в документе?",
    "🏗️ Опиши структуру документа",
]


def _render_dots_prompts(image, execution_mode: str, selected_model: str):
    """Render official dots.ocr prompt buttons."""
    st.divider()
    st.subheader("🎯 Официальные промпты dots.ocr")
    st.caption("Используйте эти промпты для лучших результатов с dots.ocr")

    for button_text, prompt_info in _OFFICIAL_PROMPTS.items():
        if st.button(
            button_text,
            help=prompt_info["description"],
            use_container_width=True,
            key=f"official_prompt_{button_text}",
        ):
            official_prompt = prompt_info["prompt"]
            st.session_state.messages.append(
                {"role": "user", "content": official_prompt}
            )
            st.session_state.current_prompt_info = prompt_info

            with st.spinner("🔄 Обрабатываем официальный промпт..."):
                response = process_official_prompt(
                    image, official_prompt, execution_mode, selected_model
                )

                if "❌" not in response:
                    st.session_state.last_ocr_result = {
                        "text": response,
                        "prompt_info": prompt_info,
                        "image": image,
                        "processing_time": 0,
                    }
                    st.success(f"✅ Официальный промпт '{button_text}' выполнен!")
                else:
                    st.warning(
                        f"⚠️ Официальный промпт '{button_text}' " "выполнен с ошибками"
                    )

                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
            st.rerun()

    st.divider()
    st.info("💡 **Новые возможности dots.ocr:**")
    st.markdown(
        "- 🔍 **BBOX визуализация** — автоматическое выделение "
        "обнаруженных элементов\n"
        "- 🖼️ **Обнаружение графики** — поиск печатей, подписей, "
        "фото, логотипов\n"
        "- 📊 **HTML таблицы** — автоматический рендеринг таблиц\n"
        "- 📐 **Layout detection** — обнаружение структуры документа\n"
        "- 🎯 **JSON структуры** — структурированный вывод с координатами"
    )


def _render_chat_examples():
    """Render example chat questions for non-dots models."""
    st.divider()
    st.subheader("💬 Примеры вопросов")
    st.caption("Попробуйте эти вопросы для интерактивного чата")

    for example in _CHAT_EXAMPLES:
        if st.button(example, use_container_width=True, key=f"chat_example_{example}"):
            st.session_state.example_prompt = example.split(" ", 1)[1]
            st.rerun()


def _handle_example_prompt(image, execution_mode: str, selected_model: str):
    """Handle a pending example prompt from session state."""
    st.info(f"💡 Предлагаемый вопрос: {st.session_state.example_prompt}")

    if st.button("✅ Использовать этот вопрос", key="use_example"):
        prompt = st.session_state.example_prompt
        del st.session_state.example_prompt

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("🤔 Думаю..."):
            if image is not None:
                response = process_prompt(image, prompt, execution_mode, selected_model)
            else:
                response = (
                    "❌ Изображение не загружено. " "Пожалуйста, загрузите изображение."
                )
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    if st.button("❌ Отменить", key="cancel_example"):
        del st.session_state.example_prompt
        st.rerun()


def show_chat(config: dict, execution_mode: str, selected_model: str) -> None:
    """Render the 💬 Режим чата page."""
    st.header("💬 Интерактивный чат с VLM")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🖼️ Загрузить изображение")

        chat_image = st.file_uploader(
            "Изображение для контекста чата",
            type=config.get("ocr", {}).get(
                "supported_formats", ["jpg", "jpeg", "png", "bmp", "tiff"]
            ),
            key="chat_upload",
        )

        image = None
        if chat_image:
            image = Image.open(chat_image)
            st.session_state.uploaded_image = image
            st.image(image, caption="Контекстное изображение", use_container_width=True)

            if "dots" in selected_model.lower():
                _render_dots_prompts(image, execution_mode, selected_model)
            else:
                _render_chat_examples()

            if st.button("🗑️ Очистить историю чата", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    with col2:
        st.subheader("💭 Разговор")

        chat_container = st.container(height=400)
        with chat_container:
            if not st.session_state.messages:
                st.info("👋 Загрузите изображение и начните " "задавать вопросы о нем!")

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    render_message_with_json_and_html_tables(
                        message["content"], message["role"]
                    )
                    if message["role"] == "assistant" and hasattr(
                        st.session_state, "last_ocr_result"
                    ):
                        display_bbox_visualization_improved(
                            st.session_state.last_ocr_result
                        )

        placeholder = (
            "Введите вопрос или используйте официальные промпты выше..."
            if "dots" in selected_model.lower()
            else "Спросите об изображении..."
        )

        # Handle pending example prompt
        if hasattr(st.session_state, "example_prompt"):
            _handle_example_prompt(
                image or st.session_state.get("uploaded_image"),
                execution_mode,
                selected_model,
            )

        # Main chat input
        if prompt := st.chat_input(placeholder, disabled=not chat_image):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🤔 Думаю..."):
                    response = process_prompt(
                        image, prompt, execution_mode, selected_model
                    )
                    render_message_with_json_and_html_tables(response, "assistant")

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
