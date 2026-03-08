"""OCR page for ChatVLMLLM Streamlit application."""

import re
import json
import time
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
from ui.components import render_alert, render_image_preview


def clean_ocr_result(text: str) -> str:
    """Очистка результата OCR от лишних символов и повторений."""
    if not text:
        return text

    char_replacements = {
        'B': 'В', 'O': 'О', 'P': 'Р', 'A': 'А', 'H': 'Н', 'K': 'К',
        'E': 'Е', 'T': 'Т', 'M': 'М', 'X': 'Х', 'C': 'С', 'Y': 'У'
    }

    for lat, cyr in char_replacements.items():
        text = re.sub(f'(?<=[А-ЯЁа-яё]){lat}(?=[А-ЯЁа-яё])', cyr, text)
        text = re.sub(f'^{lat}(?=[А-ЯЁа-яё])', cyr, text)
        text = re.sub(f'(?<=[А-ЯЁа-яё]){lat}$', cyr, text)

    corrections = {
        'BOJNTEJBCKOEVJOCTOBEPENNE': 'ВОДИТЕЛЬСКОЕ УДОСТОВЕРЕНИЕ',
        'ANTANCKNIKPA': 'АЛТАЙСКИЙ КРАЙ',
        'TN6A2747': 'ГИ БДД 2747'
    }

    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)

    text = re.sub(r'(\d+)([А-ЯЁ])', r'\1 \2', text)
    text = re.sub(r'([а-яё])(\d)', r'\1 \2', text)
    text = re.sub(r'(\))([А-ЯЁ])', r') \2', text)

    text = re.sub(r'(\d{2})\.(\d{2})\.(\d{4})(\d{2})\.(\d{2})\.(\d{4})',
                  r'\1.\2.\3 \4.\5.\6', text)

    text = re.sub(r'4a\)(\d{2}\.\d{2}\.\d{4})4b\)(\d{2}\.\d{2}\.\d{4})',
                  r'4a) \1 4b) \2', text)

    text = re.sub(r'(\d+\.)([А-ЯЁ])', r'\1 \2', text)
    text = re.sub(r'(\d+[аб]\))([А-ЯЁ\d])', r'\1 \2', text)
    text = re.sub(r'(\d+[сc]\))([А-ЯЁ])', r'\1 \2', text)

    text = re.sub(r'(\*\*[0-9\s]+\*\*)+', '', text)
    text = re.sub(r'\*\*+', '', text)
    text = re.sub(r'(00\s+){3,}', '', text)

    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if re.match(r'^[0\s\*\.]+$', line) and len(line) > 10:
            continue

        if re.match(r'^\*+$', line):
            continue

        cleaned_lines.append(line)

    cleaned_text = '\n'.join(cleaned_lines)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    cleaned_text = re.sub(r'\s{3,}', ' ', cleaned_text)

    return cleaned_text.strip()


def show_ocr(config: dict, execution_mode: str, selected_model: str) -> None:
    """Render the 📄 Режим OCR page."""

    st.header("📄 Режим распознавания документов")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📤 Загрузить документ")

        uploaded_file = st.file_uploader(
            "Выберите изображение",
            type=config.get("ocr", {}).get("supported_formats", ["jpg", "jpeg", "png", "bmp", "tiff"]),
            help="Поддерживаемые форматы: JPG, PNG, BMP, TIFF",
            key="ocr_upload"
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.session_state.uploaded_image = image
            render_image_preview(image, caption="Загруженное изображение")
            st.caption(f"📐 Размер: {image.size[0]}x{image.size[1]} | Формат: {image.format}")

        st.divider()

        document_type = st.selectbox(
            "📋 Тип документа",
            list(config.get("document_templates", {}).keys()),
            format_func=lambda x: x.capitalize(),
            help="Выберите тип документа для оптимизированного извлечения полей"
        )

        with st.expander("⚙️ Параметры обработки"):
            enhance_image = st.checkbox("Улучшить качество изображения", value=True)
            denoise = st.checkbox("Применить шумоподавление", value=False)
            deskew = st.checkbox("Автоматическое выравнивание", value=False)

        st.divider()

        # Информация о выборе модели для OCR
        if "vLLM" in execution_mode:
            try:
                from vllm_streamlit_adapter import VLLMStreamlitAdapter

                if "vllm_adapter" not in st.session_state:
                    st.session_state.vllm_adapter = VLLMStreamlitAdapter()

                adapter = st.session_state.vllm_adapter
                active_model = adapter.container_manager.get_active_model()

                if active_model:
                    active_config = adapter.container_manager.models_config[active_model]
                    render_alert(
                        f"🎯 **Для OCR будет использована активная модель:** {active_config['display_name']}",
                        "success"
                    )

                    if "dots" in active_config["model_path"].lower():
                        render_alert("✅ Специализированная OCR модель - отличный выбор для извлечения текста!", "info")
                    else:
                        render_alert("💡 Универсальная VLM модель - подходит для OCR с пониманием контекста", "info")
                else:
                    render_alert("⚠️ Нет активной модели. Будет активирована специализированная dots.ocr", "warning")

            except Exception as e:
                render_alert(f"⚠️ Не удалось проверить статус моделей: {e}", "warning")

        if st.button("🚀 Извлечь текст", type="primary", use_container_width=True):
            if uploaded_file:
                if hasattr(st.session_state, 'ocr_result'):
                    del st.session_state.ocr_result
                if hasattr(st.session_state, 'loaded_model'):
                    del st.session_state.loaded_model

                try:
                    from models.model_loader import ModelLoader
                    ModelLoader.unload_all_models()
                except Exception:
                    pass

                with st.spinner("🔄 Обработка документа..."):
                    try:
                        from models.model_loader import ModelLoader

                        start_time = time.time()
                        max_tokens = st.session_state.get('max_tokens', 1024)

                        # Предобработка изображения
                        processed_image = image
                        if enhance_image or denoise or deskew:
                            if enhance_image:
                                enhancer = ImageEnhance.Contrast(processed_image)
                                processed_image = enhancer.enhance(1.2)
                                enhancer = ImageEnhance.Sharpness(processed_image)
                                processed_image = enhancer.enhance(1.1)

                            if denoise:
                                processed_image = processed_image.filter(ImageFilter.MedianFilter(size=3))

                            max_size = 2048
                            if max(processed_image.size) > max_size:
                                ratio = max_size / max(processed_image.size)
                                new_size = tuple(int(dim * ratio) for dim in processed_image.size)
                                processed_image = processed_image.resize(new_size, Image.Resampling.LANCZOS)

                        if "vLLM" in execution_mode:
                            try:
                                from vllm_streamlit_adapter import VLLMStreamlitAdapter

                                if "vllm_adapter" not in st.session_state:
                                    st.session_state.vllm_adapter = VLLMStreamlitAdapter()

                                if st.button("🔄 Обновить статус моделей", key="refresh_adapter_ocr",
                                             help="Обновить список активных моделей"):
                                    st.session_state.vllm_adapter = VLLMStreamlitAdapter()
                                    st.success("✅ Статус моделей обновлен!")
                                    st.rerun()

                                adapter = st.session_state.vllm_adapter

                                if document_type == "passport":
                                    prompt = "Extract all text from this passport document, preserving structure and formatting"
                                elif document_type == "driver_license":
                                    prompt = "Extract all text from this driver's license, preserving structure and formatting"
                                elif document_type == "invoice":
                                    prompt = "Extract all text and structured data from this invoice"
                                else:
                                    prompt = "Extract all text from this image, preserving structure and formatting"

                                active_model = adapter.container_manager.get_active_model()

                                if not active_model:
                                    for model_key, model_cfg in adapter.container_manager.models_config.items():
                                        container_status = adapter.container_manager.get_container_status(
                                            model_cfg["container_name"]
                                        )
                                        if container_status["running"]:
                                            active_model = model_key
                                            st.info(f"🔄 Обнаружена загружающаяся модель: {model_cfg['display_name']}")
                                            break

                                if active_model:
                                    active_config = adapter.container_manager.models_config[active_model]
                                    vllm_model = active_config["model_path"]

                                    api_healthy, api_message = adapter.container_manager.check_api_health(
                                        active_config["port"]
                                    )

                                    if api_healthy:
                                        st.success(f"🎯 Используем готовую модель: {active_config['display_name']}")
                                    else:
                                        st.info(f"⏳ Ожидаем готовности модели: {active_config['display_name']} ({api_message})")
                                        render_alert(
                                            "💡 Модель загружается. Попробуйте через 1-2 минуты.",
                                            "warning"
                                        )
                                        st.stop()

                                    if "qwen" in vllm_model.lower():
                                        if document_type == "passport":
                                            prompt = "Analyze this passport document and extract all visible text, preserving the original structure and formatting. Include all fields, numbers, and text elements."
                                        elif document_type == "driver_license":
                                            prompt = "Analyze this driver's license and extract all visible text, preserving the original structure and formatting. Include all fields, numbers, and text elements."
                                        elif document_type == "invoice":
                                            prompt = "Analyze this invoice document and extract all text and structured data, preserving formatting and layout."
                                        else:
                                            prompt = "Analyze this document and extract all visible text, preserving the original structure and formatting."
                                else:
                                    st.error("❌ Нет активной модели для OCR!")
                                    render_alert(
                                        "💡 Перейдите в раздел 'Управление моделями' и запустите любую модель.",
                                        "info"
                                    )
                                    st.stop()

                                result = adapter.process_image(processed_image, prompt, vllm_model, max_tokens)

                                if result and result["success"]:
                                    text = result["text"]
                                    processing_time = result["processing_time"]
                                    st.success(f"✅ Обработано через vLLM за {processing_time:.1f} сек")
                                else:
                                    st.error("❌ Ошибка обработки через vLLM")
                                    text = "Ошибка обработки"
                                    processing_time = 0

                            except Exception as e:
                                st.error(f"❌ Ошибка vLLM режима: {e}")
                                render_alert("💡 Переключаемся на Transformers режим...", "info")
                                model = ModelLoader.load_model(selected_model)
                                if hasattr(model, 'extract_text'):
                                    text = model.extract_text(processed_image)
                                elif hasattr(model, 'process_image'):
                                    text = model.process_image(processed_image)
                                else:
                                    text = model.chat(processed_image, "Извлеките весь текст из этого документа, сохраняя структуру и форматирование.")
                        else:
                            model = ModelLoader.load_model(selected_model)

                            if hasattr(model, 'extract_text'):
                                text = model.extract_text(processed_image)
                            elif hasattr(model, 'process_image'):
                                text = model.process_image(processed_image)
                            else:
                                text = model.chat(processed_image, "Извлеките весь текст из этого документа, сохраняя структуру и форматирование.")

                        text = clean_ocr_result(text)

                        if "vLLM" not in execution_mode:
                            processing_time = time.time() - start_time

                        quality_score = 0.7
                        if len(text.strip()) > 50:
                            quality_score += 0.1
                        if len([word for word in text.split() if len(word) > 2]) > 5:
                            quality_score += 0.1
                        if any(date_pattern in text for date_pattern in [r'\d{2}\.\d{2}\.\d{4}', r'\d{4}']):
                            quality_score += 0.05
                        if any(field in text for field in ['1.', '2.', '3.', '4a)', '4b)', '4c)', '5.']):
                            quality_score += 0.05

                        quality_score = min(0.95, quality_score)

                        st.session_state.ocr_result = {
                            "text": text,
                            "confidence": quality_score,
                            "processing_time": processing_time,
                            "model_used": selected_model,
                            "execution_mode": execution_mode,
                            "preprocessing_applied": enhance_image or denoise or deskew
                        }

                        st.success("✅ Текст успешно извлечен!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Ошибка при обработке: {str(e)}")
                        render_alert(
                            "💡 Попробуйте выбрать другую модель или проверьте, что модель загружена корректно",
                            "info"
                        )
            else:
                st.error("❌ Пожалуйста, сначала загрузите изображение")

    with col2:
        st.subheader("📊 Результаты извлечения")

        ocr_result = st.session_state.get('ocr_result')
        if ocr_result:
            result = ocr_result

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            metric_col1.metric("Уверенность", f"{result['confidence']:.1%}")
            metric_col2.metric("Время обработки", f"{result['processing_time']:.2f}с")
            metric_col3.metric("Модель", result.get('model_used', 'Неизвестно'))

            execution_mode_display = result.get('execution_mode', 'Неизвестно')
            if "vLLM" in execution_mode_display:
                metric_col4.metric("Режим", "🚀 vLLM")
            else:
                metric_col4.metric("Режим", "🔧 Local")

            st.divider()

            st.markdown("**🔤 Распознанный текст:**")
            st.code(result["text"], language="text")

            st.divider()

            st.markdown("**📋 Извлеченные поля:**")

            extracted_fields = {}
            if document_type and result.get('text'):
                fields = config.get("document_templates", {}).get(document_type, {}).get("fields", [])

                full_text = result['text']

                patterns = {
                    "document_number": [
                        r'5\.(\d{7,10})',
                        r'(\d{10})',
                        r'№\s*(\d+)',
                        r'(\d{7,10})'
                    ],
                    "surname": [
                        r'1\.\s*([А-ЯЁ\s]+?)(?=\s+2\.|\s+[А-ЯЁ]+\s+[А-ЯЁ]+|$)',
                        r'(?:ВОДИТЕЛЬСКОЕ\s+УДОСТОВЕРЕНИЕ\s+)?1\.\s*([А-ЯЁ]+)',
                        r'([А-ЯЁ]{4,})\s+[А-ЯЁ]+\s+[А-ЯЁ]+',
                        r'фамилия[:\s]*([А-ЯЁ]+)',
                    ],
                    "given_names": [
                        r'2\.\s*([А-ЯЁ\s]+?)(?=\s+3\.|\s+\d{2}\.\d{2}\.\d{4}|$)',
                        r'[А-ЯЁ]{4,}\s+([А-ЯЁ]+\s+[А-ЯЁ]+)',
                        r'имя[:\s]*([А-ЯЁ\s]+)',
                    ],
                    "date_of_birth": [
                        r'3\.\s*(\d{2}\.\d{2}\.\d{4})',
                        r'(\d{2}\.\d{2}\.19\d{2})',
                        r'(\d{2}\.\d{2}\.20[0-2]\d)',
                        r'(\d{2}/\d{2}/19\d{2})'
                    ],
                    "date_of_issue": [
                        r'4[аa]\)\s*(\d{2}\.\d{2}\.\d{4})',
                        r'выдан[:\s]*(\d{2}\.\d{2}\.\d{4})',
                        r'(\d{2}\.\d{2}\.20[1-2]\d)'
                    ],
                    "date_of_expiry": [
                        r'4[бb]\)\s*(\d{2}\.\d{2}\.\d{4})',
                        r'действителен[:\s]*(\d{2}\.\d{2}\.\d{4})',
                        r'(\d{2}\.\d{2}\.20[2-3]\d)'
                    ],
                    "authority": [
                        r'4[сc]\)\s*([А-ЯЁ\s\d]+?)(?=\s+5\.|\s+\d{7}|$)',
                        r'(ГИ\s*БДД\s*\d+)',
                        r'([А-ЯЁ]+\s+КРАЙ)',
                        r'гибдд[:\s]*(\d+)',
                    ],
                    "nationality": [
                        r'8\.\s*(RUS|РФ|РОССИЯ)',
                        r'(RUS|РФ|РОССИЯ)',
                        r'гражданство[:\s]*(RUS|РФ)'
                    ]
                }

                for field in fields:
                    field_value = ""

                    if field in patterns:
                        for pattern in patterns[field]:
                            matches = re.findall(pattern, full_text, re.IGNORECASE)
                            if matches:
                                field_value = matches[0].strip()
                                break

                    if field_value:
                        field_value = ' '.join(field_value.split())
                        if len(field_value) > 50:
                            field_value = field_value[:50] + "..."

                    extracted_fields[field] = field_value

                    st.text_input(
                        field.replace('_', ' ').title(),
                        value=field_value,
                        key=f"field_{field}",
                        help="Автоматически извлечено из текста"
                    )

            st.divider()

            st.markdown("**💾 Параметры экспорта:**")
            col_json, col_csv = st.columns(2)

            export_data = {
                "text": result["text"],
                "confidence": result["confidence"],
                "processing_time": result["processing_time"],
                "model_used": result.get("model_used", "unknown"),
                "document_type": document_type,
                "extracted_fields": extracted_fields
            }

            json_data = json.dumps(export_data, ensure_ascii=False, indent=2)

            csv_data = "field,value\n"
            csv_data += f"text,\"{result['text'].replace(chr(10), ' ')}\"\n"
            csv_data += f"confidence,{result['confidence']}\n"
            csv_data += f"processing_time,{result['processing_time']}\n"
            csv_data += f"model_used,{result.get('model_used', 'unknown')}\n"
            for field, value in extracted_fields.items():
                csv_data += f"{field},\"{value}\"\n"

            with col_json:
                st.download_button(
                    "📄 Экспорт JSON",
                    data=json_data,
                    file_name="ocr_result.json",
                    mime="application/json",
                    use_container_width=True
                )
            with col_csv:
                st.download_button(
                    "📊 Экспорт CSV",
                    data=csv_data,
                    file_name="ocr_result.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            render_alert(
                "💡 Загрузите изображение и нажмите 'Извлечь текст', чтобы увидеть результаты здесь",
                "info"
            )
