"""BBOX visualization display for OCR results."""

import streamlit as st
from utils.constants import CATEGORY_EMOJIS, DEBUG_MODE


def display_bbox_visualization_improved(ocr_result):
    """Улучшенная функция отображения BBOX визуализации"""

    if not ocr_result:
        return

    prompt_info = ocr_result.get("prompt_info", {})

    # Проверяем, включена ли визуализация BBOX
    if not prompt_info.get("bbox_enabled", False):
        return

    try:
        # Принудительная перезагрузка модуля для получения последних изменений
        import importlib
        import sys
        if 'utils.bbox_visualizer' in sys.modules:
            importlib.reload(sys.modules['utils.bbox_visualizer'])

        from utils.bbox_visualizer import BBoxVisualizer

        # Получаем данные
        image = ocr_result.get("image")
        response_text = ocr_result.get("text", "")

        # Проверяем наличие изображения
        if image is None:
            st.warning("⚠️ Изображение не найдено для визуализации BBOX")
            return

        if DEBUG_MODE:
            # Отладочная информация
            st.info(f"📏 Размер изображения: {image.size[0]}x{image.size[1]}")

        # Инициализируем визуализатор
        visualizer = BBoxVisualizer()

        if DEBUG_MODE:
            st.info(f"📄 Длина ответа модели: {len(response_text)} символов")
            with st.expander("🔧 Начало ответа модели (для отладки)"):
                st.code(response_text[:500] + "..." if len(response_text) > 500 else response_text)

        # Обрабатываем ответ
        image_with_boxes, legend_img, elements = visualizer.process_dots_ocr_response(
            image,
            response_text,
            show_labels=True,
            create_legend_img=True
        )

        if DEBUG_MODE:
            st.info(f"🔍 Парсер нашел: {len(elements)} элементов")

        if not elements:
            st.warning("⚠️ BBOX элементы не найдены в ответе модели")
            st.info("💡 Убедитесь, что модель вернула JSON с BBOX координатами")

            if DEBUG_MODE:
                with st.expander("🔧 Отладка ответа модели"):
                    st.code(response_text[:300] + "..." if len(response_text) > 300 else response_text)
            return

        # Отображаем результаты
        st.divider()
        st.subheader("🔍 Визуализация обнаруженных элементов")

        # ТЕКСТОВОЕ отображение результатов (без HTML)
        st.markdown("**📊 Статистика:**")

        # Статистика в виде метрик
        col1, col2, col3 = st.columns(3)

        # Подсчет статистики
        categories = {}
        total_area = 0

        for element in elements:
            category = element.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1

            bbox = element.get('bbox', [0, 0, 0, 0])
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            total_area += area

        with col1:
            st.metric("Всего элементов", len(elements))

        with col2:
            st.metric("Категорий", len(categories))

        with col3:
            st.metric("Общая площадь", f"{total_area:,}")

        # Легенда в виде цветных индикаторов
        st.markdown("**🎨 Легенда категорий:**")

        # Отображаем категории в колонках
        legend_cols = st.columns(min(len(categories), 4))

        for i, (category, count) in enumerate(sorted(categories.items())):
            col_idx = i % len(legend_cols)
            emoji = CATEGORY_EMOJIS.get(category, '📄')

            with legend_cols[col_idx]:
                st.markdown(f"{emoji} **{category}**")
                st.caption(f"Элементов: {count}")

        # Основное отображение
        col1, col2 = st.columns([2, 1])

        with col1:
            st.image(image_with_boxes, caption="Изображение с BBOX", use_container_width=True)

        with col2:
            if legend_img:
                st.image(legend_img, caption="Легенда", use_container_width=True)

            # Статистика (дублируем для удобства)
            stats = visualizer.get_statistics(elements)
            st.metric("Всего элементов", stats.get('total_elements', 0))
            st.metric("Категорий", stats.get('unique_categories', 0))

        # ТЕКСТОВАЯ детальная информация (без HTML)
        st.markdown("### 📋 Детальная информация")

        # Отображаем элементы в виде карточек
        for i, element in enumerate(elements, 1):
            bbox = element.get('bbox', [0, 0, 0, 0])
            category = element.get('category', 'Unknown')
            text = element.get('text', '')

            # Эмодзи для категории
            emoji = CATEGORY_EMOJIS.get(category, '📄')

            # Форматирование BBOX
            bbox_str = f"[{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]"

            # Ограничение длины текста
            display_text = text[:100] + "..." if len(text) > 100 else text

            # Отображение элемента в контейнере
            with st.container():
                col_num, col_cat, col_bbox, col_text = st.columns([0.5, 1.5, 2, 4])

                with col_num:
                    st.markdown(f"**{i}**")

                with col_cat:
                    st.markdown(f"{emoji} {category}")

                with col_bbox:
                    st.code(bbox_str)

                with col_text:
                    if display_text:
                        st.caption(display_text)
                    else:
                        st.caption("_Нет текста_")

                if i < len(elements):
                    st.markdown("---")

    except Exception as e:
        st.error(f"❌ Ошибка визуализации BBOX: {str(e)}")
