"""Sidebar UI for ChatVLMLLM Streamlit application."""

import time

import streamlit as st


def render_sidebar(config: dict) -> tuple:
    """
    Render the application sidebar.

    Returns:
        tuple: (page, execution_mode, selected_model)
    """
    with st.sidebar:
        st.title("🔬 Навигация")

        page = st.radio(
            "Выберите режим",
            ["🏠 Главная", "📄 Режим OCR", "💬 Режим чата", "📚 Документация"],
            label_visibility="collapsed",
        )

        st.divider()

        st.subheader("⚙️ Настройки модели")

        # Выбор режима работы
        execution_mode = st.selectbox(
            "🚀 Режим выполнения",
            ["vLLM (Рекомендуется)", "Transformers (Локально)"],
            index=0,
            help="vLLM - высокая производительность через Docker, Transformers - локальная загрузка моделей",
        )

        # Динамический выбор модели в зависимости от режима
        if "vLLM" in execution_mode:
            # vLLM режим с интегрированным управлением контейнерами
            try:
                from single_container_manager import SingleContainerManager
                from vllm_streamlit_adapter import VLLMStreamlitAdapter

                if "vllm_adapter" not in st.session_state:
                    st.session_state.vllm_adapter = VLLMStreamlitAdapter()

                # ИСПРАВЛЕНИЕ: Кнопка принудительного обновления статуса моделей
                if st.button(
                    "🔄 Обновить статус моделей",
                    help="Принудительно обновить список активных контейнеров",
                    key="refresh_models_sidebar",
                ):
                    st.session_state.vllm_adapter = VLLMStreamlitAdapter()
                    if "single_container_manager" in st.session_state:
                        st.session_state.single_container_manager = (
                            SingleContainerManager()
                        )
                    st.success("✅ Статус моделей обновлен!")
                    st.rerun()

                if "single_container_manager" not in st.session_state:
                    st.session_state.single_container_manager = SingleContainerManager()

                # ИСПРАВЛЕНИЕ: Принудительное обновление менеджера при изменении кода
                # Проверяем, есть ли метод _build_docker_command (новый метод)
                container_manager = st.session_state.single_container_manager
                if not hasattr(container_manager, "_build_docker_command"):
                    st.warning("🔄 Обновление менеджера контейнеров...")
                    st.session_state.single_container_manager = SingleContainerManager()
                    container_manager = st.session_state.single_container_manager

                adapter = st.session_state.vllm_adapter

                # Получаем статус системы
                system_status = container_manager.get_system_status()

                # Отображаем статус активной модели
                if system_status["active_model"]:
                    st.success(
                        f"🟢 **Активная модель:** {system_status['active_model_name']}"
                    )
                    st.caption(
                        f"💾 Использование памяти: {system_status['total_memory_usage']} ГБ"
                    )

                    # Получаем активную модель для селектора
                    active_config = container_manager.models_config[
                        system_status["active_model"]
                    ]
                    selected_model = active_config["model_path"]
                    # ИСПРАВЛЕНИЕ: Используем активную модель из менеджера
                    active_model_key = adapter.container_manager.get_active_model()
                    if active_model_key:
                        active_config = adapter.container_manager.models_config[
                            active_model_key
                        ]
                        vllm_model = active_config["model_path"]
                        model_max_tokens = adapter.get_model_max_tokens(vllm_model)
                    else:
                        model_max_tokens = 1024  # Безопасное значение по умолчанию

                    # Показываем информацию об активной модели
                    st.info(
                        f"**🚀 vLLM: {selected_model.split('/')[-1]}**\n\n"
                        f"🟢 Активна и готова к работе\n"
                        f"🎯 Max Tokens: {model_max_tokens}\n"
                        f"📏 Модель: {selected_model}\n"
                        f"⚡ Принцип: Один активный контейнер"
                    )

                else:
                    st.warning("🟡 **Нет активной модели**")
                    st.info("💡 Выберите модель для активации ниже")
                    selected_model = "rednote-hilab/dots.ocr"  # Fallback
                    model_max_tokens = 1024

                # Интерфейс выбора модели с автоматическим переключением
                st.markdown("### 🎯 Управление моделями vLLM")

                # Создаем список доступных моделей
                model_options = []
                model_keys = []

                for model_key, config in container_manager.models_config.items():
                    status_icon = (
                        "🟢" if model_key == system_status["active_model"] else "⚪"
                    )
                    option_text = f"{status_icon} {config['display_name']} ({config['memory_gb']} ГБ)"
                    model_options.append(option_text)
                    model_keys.append(model_key)

                # Находим индекс активной модели
                current_index = 0
                if system_status["active_model"]:
                    try:
                        current_index = model_keys.index(system_status["active_model"])
                    except ValueError:
                        current_index = 0

                selected_model_index = st.selectbox(
                    "Выберите модель:",
                    range(len(model_options)),
                    format_func=lambda x: model_options[x],
                    index=current_index,
                    help="Выбранная модель будет запущена, все остальные остановлены",
                    key="vllm_model_selector",
                )

                selected_model_key = model_keys[selected_model_index]
                selected_config = container_manager.models_config[selected_model_key]
                selected_model = selected_config["model_path"]

                # Информация о выбранной модели
                with st.expander(f"ℹ️ Информация о {selected_config['display_name']}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Модель:** {selected_config['model_path']}")
                        st.write(f"**Порт:** {selected_config['port']}")
                        st.write(f"**Память:** {selected_config['memory_gb']} ГБ")

                    with col2:
                        st.write(
                            f"**Время запуска:** ~{selected_config['startup_time']} сек"
                        )
                        st.write(f"**Контейнер:** {selected_config['container_name']}")

                    st.write(f"**Описание:** {selected_config['description']}")

                # Кнопка переключения модели
                if selected_model_key != system_status["active_model"]:
                    if st.button(
                        f"🔄 Переключиться на {selected_config['display_name']}",
                        type="primary",
                    ):
                        with st.spinner("Переключение модели..."):
                            success, message = container_manager.start_single_container(
                                selected_model_key
                            )

                            if success:
                                st.success(message)
                                st.balloons()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(message)
                else:
                    st.success("✅ Выбранная модель уже активна")

                # Получаем лимит токенов для выбранной модели
                # ИСПРАВЛЕНИЕ: Используем активную модель из менеджера

                active_model_key = adapter.container_manager.get_active_model()
                if active_model_key:
                    active_config = adapter.container_manager.models_config[
                        active_model_key
                    ]
                    vllm_model = active_config["model_path"]
                    model_max_tokens = adapter.get_model_max_tokens(vllm_model)
                else:
                    model_max_tokens = 1024  # Безопасное значение по умолчанию

                # Предупреждение о лимитах токенов
                if model_max_tokens < 2048:
                    st.warning(
                        f"⚠️ **Ограничение токенов**\n\n"
                        f"Модель поддерживает максимум **{model_max_tokens} токенов**.\n"
                        f"Увеличение лимита в настройках выше этого значения приведет к ошибкам."
                    )

            except Exception as e:
                st.error(f"❌ Ошибка подключения к vLLM: {e}")
                selected_model = "rednote-hilab/dots.ocr"  # Fallback
                model_max_tokens = 1024
        else:
            # Transformers режим - используем модели из конфигурации
            selected_model = st.selectbox(
                "Выберите модель (Transformers)",
                list(config.get("models", {}).keys()),
                format_func=lambda x: config.get("models", {})
                .get(x, {})
                .get("name", x),
                key="transformers_model_selector",
                index=(
                    0
                    if "qwen3_vl_2b" not in config.get("models", {})
                    else list(config.get("models", {}).keys()).index("qwen3_vl_2b")
                ),  # По умолчанию лучшая модель
            )

            # Display model info для Transformers
            model_info = config.get("models", {}).get(selected_model, {})
            model_max_tokens = model_info.get("max_new_tokens", 4096)

            st.info(
                f"**{model_info['name']}**\n\n"
                f"🟡 Transformers режим - локальная обработка\n"
                f"🔧 Precision: {model_info.get('precision', 'auto')}\n"
                f"⚡ Attention: {model_info.get('attn_implementation', 'auto')}\n"
                f"🎯 Max Tokens: {model_info.get('max_new_tokens', 'auto')}\n"
                f"📏 Context: {model_info.get('context_length', 'auto')}\n"
                f"🚀 Optimized for RTX 5070 Ti Blackwell"
            )

        # ДОБАВЛЕНО: Предупреждение для dots.ocr в режиме чата
        if "dots" in selected_model.lower() and "💬 Режим чата" in page:
            st.warning(
                "⚠️ **dots.ocr специализирована на OCR**\n\n"
                "Для полноценного чата об изображениях рекомендуется использовать:\n"
                "• **Qwen3-VL 2B** - лучший выбор для чата\n"
                "• **Qwen2-VL 2B** - альтернатива\n\n"
                "dots.ocr будет адаптировать ответы, но может не отвечать на все вопросы."
            )
        elif "dots" in selected_model.lower():
            st.success("✅ **dots.ocr** - отлично подходит для OCR задач!")

        st.divider()

        with st.expander("🔧 Расширенные настройки"):
            # Получаем настройки в зависимости от режима
            if "vLLM" in execution_mode:
                # vLLM режим - используем лимиты модели
                default_temp = 0.1  # vLLM обычно использует низкую температуру
                default_max_tokens = min(model_max_tokens, 1024)  # Безопасное значение
                max_context = model_max_tokens

                st.caption(
                    f"🚀 vLLM режим: Настройки оптимизированы для {selected_model}"
                )
            else:
                # Transformers режим - используем конфигурацию
                default_temp = (
                    config.get("performance", {})
                    .get("generation_settings", {})
                    .get("temperature", 0.7)
                )
                default_max_tokens = model_info.get(
                    "max_new_tokens",
                    config.get("performance", {})
                    .get("generation_settings", {})
                    .get("default_max_tokens", 4096),
                )
                max_context = model_info.get(
                    "context_length",
                    config.get("performance", {})
                    .get("generation_settings", {})
                    .get("max_context_length", 8192),
                )

            temperature = st.slider(
                "Температура",
                0.0,
                1.0,
                default_temp,
                0.1,
                help="Контролирует случайность генерации",
            )

            # Умные настройки токенов с предупреждениями
            if "vLLM" in execution_mode and model_max_tokens < 2048:
                st.warning(
                    f"⚠️ Модель поддерживает максимум {model_max_tokens} токенов"
                )
                max_tokens = st.number_input(
                    "Макс. токенов",
                    100,
                    model_max_tokens,  # Ограничиваем реальным лимитом модели
                    default_max_tokens,
                    100,
                    help=f"⚠️ ВНИМАНИЕ: Модель {selected_model} поддерживает максимум {model_max_tokens} токенов. Превышение приведет к ошибкам!",
                )
            else:
                max_tokens = st.number_input(
                    "Макс. токенов",
                    100,
                    max_context,
                    default_max_tokens,
                    100,
                    help=f"Максимальная длина генерируемого текста (модель поддерживает до {max_context} токенов)",
                )

            # Предупреждение при превышении лимита
            if "vLLM" in execution_mode and max_tokens > model_max_tokens:
                st.error(
                    f"🚨 **ОШИБКА НАСТРОЕК**\n\n"
                    f"Установлено: {max_tokens} токенов\n"
                    f"Лимит модели: {model_max_tokens} токенов\n\n"
                    f"Это приведет к ошибкам при обработке!"
                )

            # Сохраняем в session_state для использования в других частях приложения
            st.session_state.max_tokens = max_tokens
            st.session_state.temperature = temperature
            use_gpu = st.checkbox(
                "Использовать GPU",
                value=True,
                help="Включить ускорение GPU если доступно",
            )

            # Показываем информацию о памяти
            if "vLLM" in execution_mode:
                st.caption(f"🚀 vLLM: Модель работает в Docker контейнере")
            else:
                vram_info = config.get("gpu_requirements", {}).get("rtx_5070_ti", {})
                if vram_info:
                    st.caption(
                        f"💾 VRAM: {vram_info.get('vram_total', '12GB')} общий, ~{vram_info.get('vram_available', '3GB')} доступно"
                    )

        st.divider()

        # Кнопка перезагрузки конфигурации
        if st.button(
            "🔄 Перезагрузить конфигурацию",
            help="Обновить настройки моделей",
            use_container_width=True,
        ):
            st.success("Конфигурация перезагружена!")
            st.rerun()

        # Project stats
        vllm_count = len(config.get("vllm", {}))
        transformers_count = len(config.get("transformers", {}))
        total_models = vllm_count + transformers_count

        st.markdown("### 📊 Статистика проекта")
        col1, col2 = st.columns(2)
        col1.metric("Модели", str(total_models))
        col2.metric("Статус", "✅ Готов")

        # Model loading status
        try:
            from models.model_loader import ModelLoader

            loaded_models = ModelLoader.get_loaded_models()

            if loaded_models:
                st.success(f"✅ Загружено моделей: {len(loaded_models)}")
                for model in loaded_models:
                    st.caption(f"• {model}")
            else:
                st.warning("⚠️ Модели не загружены")

            # Кнопка для выгрузки всех моделей
            if loaded_models and st.button(
                "🗑️ Выгрузить все модели", use_container_width=True
            ):
                ModelLoader.unload_all_models()
                st.success("Все модели выгружены")
                st.rerun()

        except Exception as e:
            st.error(f"Ошибка проверки моделей: {e}")

        # Тест HTML рендеринга
        st.divider()
        st.subheader("🧪 Тест HTML")

        if st.button("Тест HTML таблицы"):
            # Простая HTML таблица
            test_html = """
            <table style="border-collapse: collapse; width: 100%; border: 1px solid #ddd;">
                <tr style="background-color: #4CAF50; color: white;">
                    <th style="border: 1px solid #ddd; padding: 4px;">№</th>
                    <th style="border: 1px solid #ddd; padding: 4px;">Тест</th>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 4px;">1</td>
                    <td style="border: 1px solid #ddd; padding: 4px;">HTML работает</td>
                </tr>
            </table>
            """

            st.markdown("**HTML код:**")
            st.code(test_html[:100] + "...", language="html")
            st.markdown("**Результат:**")
            st.markdown(test_html, unsafe_allow_html=True)

        return page, execution_mode, selected_model
