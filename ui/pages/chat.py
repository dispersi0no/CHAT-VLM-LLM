"""Chat page for ChatVLMLLM Streamlit application."""

import re
import time
import streamlit as st
from PIL import Image
from ui.message_renderer import render_message_with_json_and_html_tables
from ui.bbox_display import display_bbox_visualization_improved


def show_chat(config: dict, execution_mode: str, selected_model: str) -> None:
    """Render the 💬 Режим чата page."""
    st.header("💬 Интерактивный чат с VLM")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🖼️ Загрузить изображение")
        
        chat_image = st.file_uploader(
            "Изображение для контекста чата",
            type=config.get("ocr", {}).get("supported_formats", ["jpg", "jpeg", "png", "bmp", "tiff"]),
            key="chat_upload"
        )
        
        if chat_image:
            image = Image.open(chat_image)
            st.session_state.uploaded_image = image
            st.image(image, caption="Контекстное изображение", use_container_width=True)
            
            # ДОБАВЛЕНО: Официальные промпты dots.ocr
            if "dots" in selected_model.lower():
                st.divider()
                st.subheader("🎯 Официальные промпты dots.ocr")
                st.caption("Используйте эти промпты для лучших результатов с dots.ocr")
                
                # Новые официальные промпты с BBOX возможностями
                official_prompts = {
                    "🔍 Полный анализ с BBOX": {
                        "prompt": """Please output the layout information from the PDF image, including each layout element's bbox, its category, and the corresponding text content within the bbox.

    1. Bbox format: [x1, y1, x2, y2]

    2. Layout Categories: The possible categories are ['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', 'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title'].

    3. Text Extraction & Formatting Rules:
    - Picture: For the 'Picture' category, the text field should be omitted.
    - Formula: Format its text as LaTeX.
    - Table: Format its text as HTML.
    - All Others (Text, Title, etc.): Format their text as Markdown.

    4. Constraints:
    - The output text must be the original text from the image, with no translation.
    - All layout elements must be sorted according to human reading order.

    5. Final Output: The entire output must be a single JSON object.""",
                        "description": "Полный анализ документа с BBOX координатами всех элементов",
                        "bbox_enabled": True
                    },
                    "🖼️ Обнаружение изображений": {
                        "prompt": """Analyze this document image and detect all visual elements including pictures, logos, stamps, signatures, and other graphical content. For each detected element, provide:

    1. Bbox coordinates in format [x1, y1, x2, y2]
    2. Category (Picture, Logo, Stamp, Signature, Barcode, QR-code, etc.)
    3. Brief description of the visual element

    Output as JSON array with detected visual elements.""",
                        "description": "Специализированное обнаружение графических элементов (печати, подписи, фото)",
                        "bbox_enabled": True
                    },
                    "📊 Структурированные таблицы": {
                        "prompt": """Extract and format all table content from this document as structured HTML tables with proper formatting. Include:

    1. All table data with correct row and column structure
    2. Preserve headers and data relationships
    3. Format as clean HTML tables
    4. Include bbox coordinates for each table: [x1, y1, x2, y2]

    Output format: JSON with tables array containing bbox and html_content for each table.""",
                        "description": "Извлечение таблиц с HTML форматированием и BBOX",
                        "bbox_enabled": True,
                        "table_processing": True
                    },
                    "📐 Только обнаружение (BBOX)": {
                        "prompt": """Perform layout detection only. Identify and locate all layout elements in the document without text recognition. For each element provide:

    1. Bbox coordinates: [x1, y1, x2, y2]
    2. Category from: ['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', 'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title']
    3. Confidence score if available

    Output as JSON array of detected layout elements.""",
                        "description": "Только обнаружение элементов без распознавания текста",
                        "bbox_enabled": True
                    },
                    "🔤 Простое OCR": {
                        "prompt": "Extract all text from this image.",
                        "description": "Быстрое извлечение всего текста",
                        "bbox_enabled": False
                    },
                    "📋 Чтение по порядку": {
                        "prompt": "Extract all text content from this image while maintaining reading order. Exclude headers and footers.",
                        "description": "Извлечение текста с сохранением порядка чтения",
                        "bbox_enabled": False
                    }
                }
                
                # Создаем кнопки для официальных промптов
                for button_text, prompt_info in official_prompts.items():
                    if st.button(
                        button_text,
                        help=prompt_info["description"],
                        use_container_width=True,
                        key=f"official_prompt_{button_text}"
                    ):
                        # Добавляем официальный промпт в чат
                        official_prompt = prompt_info["prompt"]
                        st.session_state.messages.append({"role": "user", "content": official_prompt})
                        
                        # Сохраняем информацию о промпте для обработки
                        st.session_state.current_prompt_info = prompt_info
                        
                        # Обрабатываем промпт
                        with st.spinner("🔄 Обрабатываем официальный промпт..."):
                            try:
                                import time
                                import torch
                                import gc
                                
                                # Принудительная очистка GPU памяти перед обработкой
                                if torch.cuda.is_available():
                                    torch.cuda.empty_cache()
                                    torch.cuda.synchronize()
                                
                                # Сборка мусора
                                gc.collect()
                                
                                # Принудительная выгрузка предыдущих моделей
                                try:
                                    from models.model_loader import ModelLoader
                                    ModelLoader.unload_all_models()
                                except:
                                    pass
                                
                                start_time = time.time()
                                
                                if "vLLM" in execution_mode:
                                    from vllm_streamlit_adapter import VLLMStreamlitAdapter
                                    
                                    if "vllm_adapter" not in st.session_state:
                                        st.session_state.vllm_adapter = VLLMStreamlitAdapter()
                                    
                                    adapter = st.session_state.vllm_adapter
                                    
                                    # Получаем настройки из session_state
                                    max_tokens = st.session_state.get('max_tokens', 4096)
                                    
                                    # ИСПРАВЛЕНИЕ: Для официальных промптов используем безопасный лимит токенов
                                    # Учитываем, что промпт + изображение занимают ~100-500 токенов
                                    model_max_tokens = adapter.get_model_max_tokens("rednote-hilab/dots.ocr")
                                    safe_max_tokens = min(max_tokens, model_max_tokens - 500)  # Резерв для входных токенов
                                    
                                    if safe_max_tokens < 100:
                                        safe_max_tokens = model_max_tokens // 2  # Используем половину как безопасное значение
                                    
                                    st.info(f"🎯 Используем {safe_max_tokens} токенов для официального промпта (лимит модели: {model_max_tokens})")
                                    
                                    # Попытка обработки с dots.ocr
                                    try:
                                        result = adapter.process_image(image, official_prompt, "rednote-hilab/dots.ocr", safe_max_tokens)
                                    except Exception as dots_error:
                                        st.warning(f"⚠️ Ошибка dots.ocr: {dots_error}")
                                        st.info("🔄 Переключаемся на Qwen3-VL для обработки...")
                                        # Fallback на Qwen3-VL
                                        try:
                                            result = adapter.process_image(image, official_prompt, "Qwen/Qwen3-VL-2B-Instruct", max_tokens)
                                            if result and result["success"]:
                                                result["text"] += "\n\n*⚠️ Обработано через Qwen3-VL (fallback)*"
                                        except Exception as fallback_error:
                                            st.error(f"❌ Ошибка fallback модели: {fallback_error}")
                                            result = {"success": False, "text": "Ошибка обработки"}
                                    
                                    if result and result["success"]:
                                        response = result["text"]
                                        processing_time = result["processing_time"]
                                        response += f"\n\n*🎯 Официальный промпт dots.ocr обработан за {processing_time:.2f}с*"
                                    else:
                                        response = "❌ Ошибка обработки официального промпта"
                                else:
                                    # Transformers режим с улучшенной обработкой ошибок
                                    from models.model_loader import ModelLoader
                                    
                                    try:
                                        model = ModelLoader.load_model(selected_model)
                                        
                                        if hasattr(model, 'process_image'):
                                            response = model.process_image(image, prompt=official_prompt)
                                        else:
                                            response = model.process_image(image)
                                        
                                        processing_time = time.time() - start_time
                                        response += f"\n\n*🔧 Официальный промпт обработан локально за {processing_time:.2f}с*"
                                        
                                    except RuntimeError as cuda_error:
                                        if "CUDA error" in str(cuda_error) or "device-side assert" in str(cuda_error):
                                            st.error("❌ Ошибка GPU. Попробуйте перезагрузить страницу или выбрать другую модель.")
                                            st.info("💡 Рекомендация: Используйте vLLM режим для более стабильной работы.")
                                            response = f"❌ Ошибка GPU: {str(cuda_error)}"
                                        else:
                                            response = f"❌ Ошибка выполнения: {str(cuda_error)}"
                                    
                                    except Exception as model_error:
                                        if "video_processor" in str(model_error) or "NoneType" in str(model_error):
                                            st.error("❌ Ошибка загрузки dots.ocr. Попробуйте использовать Qwen3-VL.")
                                            response = "❌ Ошибка загрузки модели dots.ocr"
                                        else:
                                            response = f"❌ Ошибка модели: {str(model_error)}"
                                
                                # Сохраняем результат для дальнейшей обработки BBOX и таблиц
                                if "❌" not in response and hasattr(st.session_state, 'current_prompt_info'):
                                    st.session_state.last_ocr_result = {
                                        "text": response,
                                        "prompt_info": st.session_state.current_prompt_info,
                                        "image": image,
                                        "processing_time": processing_time if 'processing_time' in locals() else 0
                                    }
                                
                                # Добавляем ответ в чат
                                st.session_state.messages.append({"role": "assistant", "content": response})
                                
                                if "❌" not in response:
                                    st.success(f"✅ Официальный промпт '{button_text}' выполнен!")
                                else:
                                    st.warning(f"⚠️ Официальный промпт '{button_text}' выполнен с ошибками")
                                
                                st.rerun()
                                
                            except RuntimeError as e:
                                if "CUDA error" in str(e) or "device-side assert" in str(e):
                                    error_response = "❌ Критическая ошибка GPU. Перезагрузите страницу и попробуйте vLLM режим."
                                    st.error("❌ Ошибка GPU. Попробуйте перезагрузить страницу или выбрать другую модель.")
                                    st.info("💡 Рекомендация: Используйте vLLM режим для более стабильной работы.")
                                else:
                                    error_response = f"❌ Ошибка выполнения: {str(e)}"
                                    st.error(f"❌ Ошибка выполнения: {str(e)}")
                                
                                st.session_state.messages.append({"role": "assistant", "content": error_response})
                                st.rerun()
                                
                            except Exception as e:
                                error_response = f"❌ Неожиданная ошибка при выполнении официального промпта: {str(e)}"
                                st.session_state.messages.append({"role": "assistant", "content": error_response})
                                st.error(f"❌ Неожиданная ошибка: {str(e)}")
                                st.info("💡 Попробуйте обновить страницу или выбрать другую модель.")
                                st.rerun()
                
                st.divider()
                st.info("💡 **Новые возможности dots.ocr:**")
                st.markdown("""
                - 🔍 **BBOX визуализация** - автоматическое выделение обнаруженных элементов
                - 🖼️ **Обнаружение графики** - поиск печатей, подписей, фото, логотипов
                - 📊 **HTML таблицы** - автоматический рендеринг таблиц из ответов
                - 📐 **Layout detection** - обнаружение структуры документа
                - 🎯 **JSON структуры** - структурированный вывод с координатами
                """)
            
            else:
                # Для других моделей показываем примеры чат-вопросов
                st.divider()
                st.subheader("💬 Примеры вопросов")
                st.caption("Попробуйте эти вопросы для интерактивного чата")
                
                chat_examples = [
                    "🔍 Что изображено на картинке?",
                    "📝 Опиши содержимое документа",
                    "🔢 Найди все числа в изображении",
                    "📊 Есть ли таблицы в документе?",
                    "🏗️ Опиши структуру документа"
                ]
                
                for example in chat_examples:
                    if st.button(
                        example,
                        use_container_width=True,
                        key=f"chat_example_{example}"
                    ):
                        # Добавляем пример в поле ввода (через session state)
                        st.session_state.example_prompt = example.split(" ", 1)[1]  # Убираем эмодзи
                        st.rerun()
            
            if st.button("🗑️ Очистить историю чата", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    with col2:
        st.subheader("💭 Разговор")
        
        # Chat container
        chat_container = st.container(height=400)
        
        with chat_container:
            if not st.session_state.messages:
                st.info("👋 Загрузите изображение и начните задавать вопросы о нем!")
            
            # Display chat messages - HTML РЕНДЕРИНГ РАБОТАЕТ
            # Display chat messages - ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ HTML
            for i, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    # ИСПОЛЬЗУЕМ НОВУЮ НАДЕЖНУЮ ФУНКЦИЮ
                    render_message_with_json_and_html_tables(message["content"], message["role"])
                    
                    # Обработка BBOX если это ответ ассистента и есть сохраненный результат OCR
                    if message["role"] == "assistant" and hasattr(st.session_state, 'last_ocr_result'):
                        ocr_result = st.session_state.last_ocr_result
                        # Обработка BBOX если включена
                        display_bbox_visualization_improved(ocr_result)
        
        # Chat input с подсказкой в зависимости от модели
        if "dots" in selected_model.lower():
            placeholder = "Введите вопрос или используйте официальные промпты выше..."
        else:
            placeholder = "Спросите об изображении..."
        
        # Показываем подсказку если есть пример
        if hasattr(st.session_state, 'example_prompt'):
            st.info(f"💡 Предлагаемый вопрос: {st.session_state.example_prompt}")
            if st.button("✅ Использовать этот вопрос", key="use_example"):
                prompt = st.session_state.example_prompt
                del st.session_state.example_prompt
                
                # Добавляем пример в чат и обрабатываем его
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Обрабатываем промпт через модель
                with st.spinner("🤔 Думаю..."):
                    try:
                        import time
                        import torch
                        import gc
                        
                        # Принудительная очистка GPU памяти перед обработкой
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                            torch.cuda.synchronize()
                        
                        # Сборка мусора
                        gc.collect()
                        
                        start_time = time.time()
                        
                        # Обработка в зависимости от режима
                        if "vLLM" in execution_mode:
                            # Получаем настройки из session_state
                            max_tokens = st.session_state.get('max_tokens', 4096)
                            temperature = st.session_state.get('temperature', 0.7)
                            
                            # vLLM режим - используем API
                            try:
                                from vllm_streamlit_adapter import VLLMStreamlitAdapter
                                
                                if "vllm_adapter" not in st.session_state:
                                    st.session_state.vllm_adapter = VLLMStreamlitAdapter()
                                
                                adapter = st.session_state.vllm_adapter
                                
                                # ИСПРАВЛЕНИЕ: Проверяем тип модели для правильной обработки
                                if "dots" in selected_model.lower():
                                    # dots.ocr специализирована на OCR, адаптируем ответ
                                    vllm_model = "rednote-hilab/dots.ocr"
                                    
                                    # Используем безопасный лимит токенов для dots.ocr
                                    model_max_tokens = adapter.get_model_max_tokens(vllm_model)
                                    safe_max_tokens = min(max_tokens, model_max_tokens - 500)  # Резерв для входных токенов
                                    
                                    if safe_max_tokens < 100:
                                        safe_max_tokens = model_max_tokens // 2
                                    
                                    result = adapter.process_image(image, prompt, vllm_model, safe_max_tokens)
                                    
                                    if result and result["success"]:
                                        ocr_text = result["text"]
                                        processing_time = result["processing_time"]
                                        
                                        # Анализируем тип вопроса и адаптируем ответ
                                        if any(word in prompt.lower() for word in ['текст', 'прочитай', 'извлеки', 'распознай', 'text', 'extract', 'read']):
                                            # OCR вопрос - возвращаем как есть
                                            response = ocr_text
                                        elif any(word in prompt.lower() for word in ['что', 'какой', 'сколько', 'есть ли', 'найди', 'what', 'how', 'is there', 'find']):
                                            # Аналитический вопрос - адаптируем ответ
                                            if 'число' in prompt.lower() or 'number' in prompt.lower():
                                                # Ищем числа в тексте
                                                numbers = re.findall(r'\d+', ocr_text)
                                                if numbers:
                                                    response = f"В изображении найдены числа: {', '.join(numbers)}"
                                                else:
                                                    response = "В изображении не найдено чисел."
                                            elif 'цвет' in prompt.lower() or 'color' in prompt.lower():
                                                response = "dots.ocr специализирована на распознавании текста, а не анализе цветов. Для анализа изображений используйте Qwen3-VL."
                                            elif 'сколько' in prompt.lower() or 'how many' in prompt.lower():
                                                words = len(ocr_text.split())
                                                response = f"В тексте примерно {words} слов."
                                            elif 'есть ли' in prompt.lower() or 'is there' in prompt.lower():
                                                if 'текст' in prompt.lower() or 'text' in prompt.lower():
                                                    response = f"Да, в изображении есть текст:\n\n{ocr_text}"
                                                else:
                                                    response = f"dots.ocr может определить только наличие текста. Найденный текст:\n\n{ocr_text}"
                                            else:
                                                # Общий аналитический вопрос
                                                response = f"dots.ocr специализирована на OCR. Вот распознанный текст, который может помочь ответить на ваш вопрос:\n\n{ocr_text}\n\n💡 Для детального анализа изображений используйте Qwen3-VL в настройках модели."
                                        else:
                                            # Неопределенный вопрос
                                            response = f"dots.ocr специализирована на распознавании текста. Извлеченный текст:\n\n{ocr_text}\n\n💡 Для чата об изображениях выберите Qwen3-VL в настройках модели."
                                        
                                        # Добавление информации о времени обработки
                                        response += f"\n\n*🚀 Обработано через vLLM за {processing_time:.2f}с*"
                                    else:
                                        response = "❌ Ошибка обработки через vLLM"
                                        processing_time = 0
                                else:
                                    # Другие модели - используем безопасный лимит токенов
                                    # ИСПРАВЛЕНИЕ: Используем активную модель из менеджера

                                    active_model_key = adapter.container_manager.get_active_model()
                                    if active_model_key:
                                        active_config = adapter.container_manager.models_config[active_model_key]
                                        vllm_model = active_config["model_path"]
                                        model_max_tokens = adapter.get_model_max_tokens(vllm_model)
                                    else:
                                        model_max_tokens = 1024  # Безопасное значение по умолчанию
                                    safe_max_tokens = min(max_tokens, model_max_tokens - 500)  # Резерв для входных токенов
                                    
                                    if safe_max_tokens < 100:
                                        safe_max_tokens = model_max_tokens // 2
                                    
                                    # ИСПРАВЛЕНИЕ: Используем активную модель из менеджера

                                    
                                    active_model_key = adapter.container_manager.get_active_model()
                                    if active_model_key:
                                        active_config = adapter.container_manager.models_config[active_model_key]
                                        vllm_model = active_config["model_path"]
                                        result = adapter.process_image(image, prompt, vllm_model, safe_max_tokens)
                                    else:
                                        st.error("❌ Нет активной модели")
                                        result = None
                                    
                                    if result and result["success"]:
                                        response = result["text"]
                                        processing_time = result["processing_time"]
                                        response += f"\n\n*🚀 Обработано через vLLM за {processing_time:.2f}с*"
                                    else:
                                        response = "❌ Ошибка обработки через vLLM"
                                        processing_time = 0
                                        
                            except Exception as e:
                                error_msg = str(e)
                                
                                # Специальная обработка CUDA ошибок
                                if "CUDA error" in error_msg or "device-side assert" in error_msg:
                                    st.error("❌ Ошибка GPU. Попробуйте перезагрузить страницу или выбрать другую модель.")
                                    st.info("💡 Рекомендация: Используйте vLLM режим для более стабильной работы.")
                                    response = "❌ Критическая ошибка GPU. Перезагрузите страницу и попробуйте vLLM режим."
                                elif "video_processor" in error_msg or "NoneType" in error_msg:
                                    st.error("❌ Ошибка загрузки dots.ocr. Попробуйте использовать Qwen3-VL.")
                                    response = "❌ Ошибка загрузки модели dots.ocr. Используйте Qwen3-VL для аналогичных задач."
                                else:
                                    st.error(f"❌ Ошибка vLLM режима: {e}")
                                    st.info("💡 Переключаемся на Transformers режим...")
                                
                                # Fallback на Transformers только если не критическая ошибка
                                if "CUDA error" not in error_msg and "device-side assert" not in error_msg:
                                    try:
                                        from models.model_loader import ModelLoader
                                        model = ModelLoader.load_model(selected_model)
                                        
                                        if hasattr(model, 'chat'):
                                            response = model.chat(
                                                image=image,
                                                prompt=prompt,
                                                temperature=temperature,
                                                max_new_tokens=max_tokens
                                            )
                                        elif hasattr(model, 'process_image'):
                                            if any(word in prompt.lower() for word in ['текст', 'прочитай', 'извлеки']):
                                                response = model.process_image(image)
                                            else:
                                                response = f"Это OCR модель. Извлеченный текст:\n\n{model.process_image(image)}"
                                        else:
                                            response = "Модель не поддерживает чат. Попробуйте режим OCR."
                                        
                                        processing_time = time.time() - start_time
                                        response += f"\n\n*🔧 Обработано локально за {processing_time:.2f}с с помощью {selected_model}*"
                                        
                                    except Exception as fallback_error:
                                        response = f"❌ Ошибка и в fallback режиме: {str(fallback_error)}"
                        else:
                            # Получаем настройки из session_state
                            max_tokens = st.session_state.get('max_tokens', 4096)
                            temperature = st.session_state.get('temperature', 0.7)
                            
                            # Transformers режим - локальная загрузка с улучшенной обработкой ошибок
                            try:
                                from models.model_loader import ModelLoader
                                model = ModelLoader.load_model(selected_model)
                                
                                # Получение ответа от модели
                                if hasattr(model, 'chat'):
                                    response = model.chat(
                                        image=image,
                                        prompt=prompt,
                                        temperature=temperature,
                                        max_new_tokens=max_tokens
                                    )
                                elif hasattr(model, 'process_image'):
                                    # Для OCR моделей адаптируем промпт
                                    if any(word in prompt.lower() for word in ['текст', 'прочитай', 'извлеки']):
                                        response = model.process_image(image)
                                    else:
                                        response = f"Это OCR модель. Извлеченный текст:\n\n{model.process_image(image)}"
                                else:
                                    response = "Модель не поддерживает чат. Попробуйте режим OCR."
                                
                                processing_time = time.time() - start_time
                                response += f"\n\n*🔧 Обработано локально за {processing_time:.2f}с с помощью {selected_model}*"
                                
                            except RuntimeError as cuda_error:
                                if "CUDA error" in str(cuda_error) or "device-side assert" in str(cuda_error):
                                    response = "❌ Критическая ошибка GPU. Перезагрузите страницу и попробуйте vLLM режим."
                                    st.error("❌ Ошибка GPU. Попробуйте перезагрузить страницу или выбрать другую модель.")
                                    st.info("💡 Рекомендация: Используйте vLLM режим для более стабильной работы.")
                                else:
                                    response = f"❌ Ошибка выполнения: {str(cuda_error)}"
                            
                            except Exception as model_error:
                                if "video_processor" in str(model_error) or "NoneType" in str(model_error):
                                    response = "❌ Ошибка загрузки модели dots.ocr. Используйте Qwen3-VL для аналогичных задач."
                                    st.error("❌ Ошибка загрузки dots.ocr. Попробуйте использовать Qwen3-VL.")
                                else:
                                    response = f"❌ Ошибка модели: {str(model_error)}"
                        
                        # Добавляем ответ в чат
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                    except Exception as e:
                        error_msg = str(e)
                        
                        if "video_processor" in error_msg or "NoneType" in error_msg:
                            response = "❌ Ошибка загрузки модели dots.ocr. Используйте Qwen3-VL для аналогичных задач."
                            st.error("❌ Ошибка загрузки dots.ocr. Попробуйте использовать Qwen3-VL.")
                        else:
                            response = f"❌ Ошибка при обработке: {error_msg}\n\n💡 Попробуйте выбрать другую модель или проверьте, что модель загружена корректно."
                        
                        # Добавляем ошибку в чат
                        st.session_state.messages.append({"role": "assistant", "content": response})
                
                st.rerun()
                
            if st.button("❌ Отменить", key="cancel_example"):
                del st.session_state.example_prompt
                st.rerun()
        
        if prompt := st.chat_input(placeholder, disabled=not chat_image):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response using real model
            with st.chat_message("assistant"):
                with st.spinner("🤔 Думаю..."):
                    try:
                        import time
                        import torch
                        import gc
                        
                        # Принудительная очистка GPU памяти перед обработкой
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                            torch.cuda.synchronize()
                        
                        # Сборка мусора
                        gc.collect()
                        
                        start_time = time.time()
                        
                        # Обработка в зависимости от режима
                        if "vLLM" in execution_mode:
                            # Получаем настройки из session_state
                            max_tokens = st.session_state.get('max_tokens', 4096)
                            temperature = st.session_state.get('temperature', 0.7)
                            
                            # vLLM режим - используем API
                            try:
                                from vllm_streamlit_adapter import VLLMStreamlitAdapter
                                
                                if "vllm_adapter" not in st.session_state:
                                    st.session_state.vllm_adapter = VLLMStreamlitAdapter()
                                
                                adapter = st.session_state.vllm_adapter
                                
                                # ИСПРАВЛЕНИЕ: Проверяем тип модели для правильной обработки
                                if "dots" in selected_model.lower():
                                    # dots.ocr специализирована на OCR, адаптируем ответ
                                    vllm_model = "rednote-hilab/dots.ocr"
                                    
                                    # Используем безопасный лимит токенов для dots.ocr
                                    model_max_tokens = adapter.get_model_max_tokens(vllm_model)
                                    safe_max_tokens = min(max_tokens, model_max_tokens - 500)  # Резерв для входных токенов
                                    
                                    if safe_max_tokens < 100:
                                        safe_max_tokens = model_max_tokens // 2
                                    
                                    result = adapter.process_image(image, prompt, vllm_model, safe_max_tokens)
                                    
                                    if result and result["success"]:
                                        ocr_text = result["text"]
                                        processing_time = result["processing_time"]
                                        
                                        # Анализируем тип вопроса и адаптируем ответ
                                        if any(word in prompt.lower() for word in ['текст', 'прочитай', 'извлеки', 'распознай', 'text', 'extract', 'read']):
                                            # OCR вопрос - возвращаем как есть
                                            response = ocr_text
                                        elif any(word in prompt.lower() for word in ['что', 'какой', 'сколько', 'есть ли', 'найди', 'what', 'how', 'is there', 'find']):
                                            # Аналитический вопрос - адаптируем ответ
                                            if 'число' in prompt.lower() or 'number' in prompt.lower():
                                                # Ищем числа в тексте
                                                numbers = re.findall(r'\d+', ocr_text)
                                                if numbers:
                                                    response = f"В изображении найдены числа: {', '.join(numbers)}"
                                                else:
                                                    response = "В изображении не найдено чисел."
                                            elif 'цвет' in prompt.lower() or 'color' in prompt.lower():
                                                response = "dots.ocr специализирована на распознавании текста, а не анализе цветов. Для анализа изображений используйте Qwen3-VL."
                                            elif 'сколько' in prompt.lower() or 'how many' in prompt.lower():
                                                words = len(ocr_text.split())
                                                response = f"В тексте примерно {words} слов."
                                            elif 'есть ли' in prompt.lower() or 'is there' in prompt.lower():
                                                if 'текст' in prompt.lower() or 'text' in prompt.lower():
                                                    response = f"Да, в изображении есть текст:\n\n{ocr_text}"
                                                else:
                                                    response = f"dots.ocr может определить только наличие текста. Найденный текст:\n\n{ocr_text}"
                                            else:
                                                # Общий аналитический вопрос
                                                response = f"dots.ocr специализирована на OCR. Вот распознанный текст, который может помочь ответить на ваш вопрос:\n\n{ocr_text}\n\n💡 Для детального анализа изображений используйте Qwen3-VL в настройках модели."
                                        else:
                                            # Неопределенный вопрос
                                            response = f"dots.ocr специализирована на распознавании текста. Извлеченный текст:\n\n{ocr_text}\n\n💡 Для чата об изображениях выберите Qwen3-VL в настройках модели."
                                        
                                        # Добавление информации о времени обработки
                                        response += f"\n\n*🚀 Обработано через vLLM за {processing_time:.2f}с*"
                                    else:
                                        response = "❌ Ошибка обработки через vLLM"
                                        processing_time = 0
                                else:
                                    # Другие модели - используем безопасный лимит токенов
                                    # ИСПРАВЛЕНИЕ: Используем активную модель из менеджера

                                    active_model_key = adapter.container_manager.get_active_model()
                                    if active_model_key:
                                        active_config = adapter.container_manager.models_config[active_model_key]
                                        vllm_model = active_config["model_path"]
                                        model_max_tokens = adapter.get_model_max_tokens(vllm_model)
                                    else:
                                        model_max_tokens = 1024  # Безопасное значение по умолчанию
                                    safe_max_tokens = min(max_tokens, model_max_tokens - 500)  # Резерв для входных токенов
                                    
                                    if safe_max_tokens < 100:
                                        safe_max_tokens = model_max_tokens // 2
                                    
                                    # ИСПРАВЛЕНИЕ: Используем активную модель из менеджера

                                    
                                    active_model_key = adapter.container_manager.get_active_model()
                                    if active_model_key:
                                        active_config = adapter.container_manager.models_config[active_model_key]
                                        vllm_model = active_config["model_path"]
                                        result = adapter.process_image(image, prompt, vllm_model, safe_max_tokens)
                                    else:
                                        st.error("❌ Нет активной модели")
                                        result = None
                                    
                                    if result and result["success"]:
                                        response = result["text"]
                                        processing_time = result["processing_time"]
                                        response += f"\n\n*🚀 Обработано через vLLM за {processing_time:.2f}с*"
                                    else:
                                        response = "❌ Ошибка обработки через vLLM"
                                        processing_time = 0
                                    
                            except Exception as e:
                                error_msg = str(e)
                                
                                # Специальная обработка CUDA ошибок
                                if "CUDA error" in error_msg or "device-side assert" in error_msg:
                                    st.error("❌ Ошибка GPU. Попробуйте перезагрузить страницу или выбрать другую модель.")
                                    st.info("💡 Рекомендация: Используйте vLLM режим для более стабильной работы.")
                                    response = "❌ Критическая ошибка GPU. Перезагрузите страницу и попробуйте vLLM режим."
                                elif "video_processor" in error_msg or "NoneType" in error_msg:
                                    st.error("❌ Ошибка загрузки dots.ocr. Попробуйте использовать Qwen3-VL.")
                                    response = "❌ Ошибка загрузки модели dots.ocr. Используйте Qwen3-VL для аналогичных задач."
                                else:
                                    st.error(f"❌ Ошибка vLLM режима: {e}")
                                    st.info("💡 Переключаемся на Transformers режим...")
                                
                                # Fallback на Transformers только если не критическая ошибка
                                if "CUDA error" not in error_msg and "device-side assert" not in error_msg:
                                    try:
                                        from models.model_loader import ModelLoader
                                        model = ModelLoader.load_model(selected_model)
                                        
                                        if hasattr(model, 'chat'):
                                            response = model.chat(
                                                image=image,
                                                prompt=prompt,
                                                temperature=temperature,
                                                max_new_tokens=max_tokens
                                            )
                                        elif hasattr(model, 'process_image'):
                                            if any(word in prompt.lower() for word in ['текст', 'прочитай', 'извлеки']):
                                                response = model.process_image(image)
                                            else:
                                                response = f"Это OCR модель. Извлеченный текст:\n\n{model.process_image(image)}"
                                        else:
                                            response = "Модель не поддерживает чат. Попробуйте режим OCR."
                                        
                                        processing_time = time.time() - start_time
                                        response += f"\n\n*🔧 Обработано локально за {processing_time:.2f}с с помощью {selected_model}*"
                                        
                                    except Exception as fallback_error:
                                        response = f"❌ Ошибка и в fallback режиме: {str(fallback_error)}"
                        else:
                            # Получаем настройки из session_state
                            max_tokens = st.session_state.get('max_tokens', 4096)
                            temperature = st.session_state.get('temperature', 0.7)
                            
                            # Transformers режим - локальная загрузка с улучшенной обработкой ошибок
                            try:
                                from models.model_loader import ModelLoader
                                model = ModelLoader.load_model(selected_model)
                                
                                # Получение ответа от модели
                                if hasattr(model, 'chat'):
                                    response = model.chat(
                                        image=image,
                                        prompt=prompt,
                                        temperature=temperature,
                                        max_new_tokens=max_tokens
                                    )
                                elif hasattr(model, 'process_image'):
                                    # Для OCR моделей адаптируем промпт
                                    if any(word in prompt.lower() for word in ['текст', 'прочитай', 'извлеки']):
                                        response = model.process_image(image)
                                    else:
                                        response = f"Это OCR модель. Извлеченный текст:\n\n{model.process_image(image)}"
                                else:
                                    response = "Модель не поддерживает чат. Попробуйте режим OCR."
                                
                                processing_time = time.time() - start_time
                                response += f"\n\n*🔧 Обработано локально за {processing_time:.2f}с с помощью {selected_model}*"
                                
                            except RuntimeError as cuda_error:
                                if "CUDA error" in str(cuda_error) or "device-side assert" in str(cuda_error):
                                    response = "❌ Критическая ошибка GPU. Перезагрузите страницу и попробуйте vLLM режим."
                                    st.error("❌ Ошибка GPU. Попробуйте перезагрузить страницу или выбрать другую модель.")
                                    st.info("💡 Рекомендация: Используйте vLLM режим для более стабильной работы.")
                                else:
                                    response = f"❌ Ошибка выполнения: {str(cuda_error)}"
                            
                            except Exception as model_error:
                                if "video_processor" in str(model_error) or "NoneType" in str(model_error):
                                    response = "❌ Ошибка загрузки модели dots.ocr. Используйте Qwen3-VL для аналогичных задач."
                                    st.error("❌ Ошибка загрузки dots.ocr. Попробуйте использовать Qwen3-VL.")
                                else:
                                    response = f"❌ Ошибка модели: {str(model_error)}"
                        
                        # HTML РЕНДЕРИНГ В ОТВЕТАХ - ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ
                        render_message_with_json_and_html_tables(response, "assistant")
                        
                    except RuntimeError as e:
                        if "CUDA error" in str(e) or "device-side assert" in str(e):
                            response = "❌ Критическая ошибка GPU. Перезагрузите страницу и попробуйте vLLM режим."
                            st.error("❌ Ошибка GPU. Попробуйте перезагрузить страницу или выбрать другую модель.")
                            st.info("💡 Рекомендация: Используйте vLLM режим для более стабильной работы.")
                        else:
                            response = f"❌ Ошибка выполнения: {str(e)}"
                        # HTML РЕНДЕРИНГ В ОТВЕТАХ - ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ
                        render_message_with_json_and_html_tables(response, "assistant")
                        
                    except Exception as e:
                        error_msg = str(e)
                        
                        if "video_processor" in error_msg or "NoneType" in error_msg:
                            response = "❌ Ошибка загрузки модели dots.ocr. Используйте Qwen3-VL для аналогичных задач."
                            st.error("❌ Ошибка загрузки dots.ocr. Попробуйте использовать Qwen3-VL.")
                        else:
                            response = f"❌ Ошибка при обработке: {error_msg}\n\n💡 Попробуйте выбрать другую модель или проверьте, что модель загружена корректно."
                        
                        # HTML РЕНДЕРИНГ В ОТВЕТАХ - ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ
                        render_message_with_json_and_html_tables(response, "assistant")
            
            # Add assistant response
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()


