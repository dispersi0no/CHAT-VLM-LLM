#!/usr/bin/env python3
"""
Утилита для визуализации BBOX координат на изображениях
"""

import colorsys
import json
import random
import re
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


class BBoxVisualizer:
    """Класс для визуализации bounding boxes на изображениях"""

    # Цвета для разных категорий элементов
    CATEGORY_COLORS = {
        "Text": "#FF6B6B",  # Красный
        "Title": "#4ECDC4",  # Бирюзовый
        "Table": "#45B7D1",  # Синий
        "Picture": "#96CEB4",  # Зеленый
        "Formula": "#FFEAA7",  # Желтый
        "Caption": "#DDA0DD",  # Сливовый
        "Footnote": "#F0A500",  # Оранжевый
        "List-item": "#FF7675",  # Розовый
        "Page-header": "#74B9FF",  # Голубой
        "Page-footer": "#A29BFE",  # Фиолетовый
        "Section-header": "#FD79A8",  # Малиновый
        "Signature": "#00B894",  # Темно-зеленый
        "Stamp": "#E17055",  # Коричневый
        "Logo": "#6C5CE7",  # Индиго
        "Barcode": "#FDCB6E",  # Золотой
        "QR-code": "#E84393",  # Пурпурный
    }

    def __init__(self):
        self.font_cache = {}

    def get_font(self, size: int = 12) -> ImageFont.ImageFont:
        """Получение шрифта с кешированием"""
        if size not in self.font_cache:
            try:
                # Попытка загрузить системный шрифт
                self.font_cache[size] = ImageFont.truetype("arial.ttf", size)
            except (OSError, IOError):
                try:
                    self.font_cache[size] = ImageFont.truetype("DejaVuSans.ttf", size)
                except (OSError, IOError):
                    # Fallback на стандартный шрифт
                    self.font_cache[size] = ImageFont.load_default()
        return self.font_cache[size]

    def parse_bbox_from_json(self, json_text: str) -> List[Dict[str, Any]]:
        """Парсинг BBOX координат из JSON ответа dots.ocr"""
        try:
            json_text_stripped = json_text.strip()

            # Удаление markdown code blocks если есть
            if json_text_stripped.startswith("```json"):
                lines = json_text_stripped.split("\n")
                json_text_stripped = (
                    "\n".join(lines[1:-1]) if len(lines) > 2 else json_text_stripped
                )
            elif json_text_stripped.startswith("```"):
                lines = json_text_stripped.split("\n")
                json_text_stripped = (
                    "\n".join(lines[1:-1]) if len(lines) > 2 else json_text_stripped
                )

            # Попытка парсинга как JSON
            if json_text_stripped.startswith("{") or json_text_stripped.startswith("["):
                try:
                    # Пытаемся найти конец JSON массива/объекта
                    import re

                    # Ищем JSON массив или объект
                    if json_text_stripped.startswith("["):
                        # Ищем закрывающую скобку массива на верхнем уровне
                        bracket_count = 0
                        in_string = False
                        escape_next = False
                        json_end = -1

                        for i, char in enumerate(json_text_stripped):
                            if escape_next:
                                escape_next = False
                                continue

                            if char == "\\":
                                escape_next = True
                                continue

                            if char == '"' and not escape_next:
                                in_string = not in_string

                            if not in_string:
                                if char == "[":
                                    bracket_count += 1
                                elif char == "]":
                                    bracket_count -= 1
                                    if bracket_count == 0:
                                        json_end = i + 1
                                        break

                        if json_end > 0:
                            json_text_stripped = json_text_stripped[:json_end]

                    data = json.loads(json_text_stripped)

                    # Если это список элементов
                    if isinstance(data, list):
                        return data

                    # Если это объект с элементами
                    if isinstance(data, dict):
                        if "elements" in data:
                            return data["elements"]
                        elif "layout" in data:
                            return data["layout"]
                        elif "items" in data:
                            return data["items"]
                        elif "data" in data:
                            return data["data"]
                        elif "bbox" in data:
                            # Возможно, это единственный элемент
                            return [data]

                    return []

                except json.JSONDecodeError as e:
                    # Если ошибка из-за управляющих символов (например \n в тексте)
                    print(
                        f"⚠️ Ошибка JSON парсинга (пытаемся исправить): {str(e)[:100]}"
                    )

                    # Попытка исправления: заменяем неэкранированные \n на пробелы
                    import re

                    def fix_newlines(match):
                        text = match.group(1)
                        # Заменяем \n и пробелы вокруг них на один пробел
                        text = re.sub(r"\s*\n\s*", " ", text)
                        # Убираем множественные пробелы
                        text = re.sub(r"\s+", " ", text)
                        return f'"text": "{text.strip()}"'

                    # Сначала пытаемся извлечь только JSON часть
                    if json_text_stripped.startswith("["):
                        bracket_count = 0
                        in_string = False
                        escape_next = False
                        json_end = -1

                        for i, char in enumerate(json_text_stripped):
                            if escape_next:
                                escape_next = False
                                continue

                            if char == "\\":
                                escape_next = True
                                continue

                            if char == '"' and not escape_next:
                                in_string = not in_string

                            if not in_string:
                                if char == "[":
                                    bracket_count += 1
                                elif char == "]":
                                    bracket_count -= 1
                                    if bracket_count == 0:
                                        json_end = i + 1
                                        break

                        if json_end > 0:
                            json_text_stripped = json_text_stripped[:json_end]

                    fixed_json = re.sub(
                        r'"text"\s*:\s*"([^"]*)"',
                        fix_newlines,
                        json_text_stripped,
                        flags=re.DOTALL,
                    )

                    try:
                        data = json.loads(fixed_json)
                        if isinstance(data, list):
                            print(f"✅ JSON исправлен, найдено {len(data)} элементов")
                            return data
                        elif isinstance(data, dict) and "bbox" in data:
                            return [data]
                    except Exception as e2:
                        print(f"⚠️ Не удалось исправить JSON: {str(e2)[:100]}")

            # Если JSON не парсится, попробуем извлечь BBOX из текста
            return self.extract_bbox_from_text(json_text)

        except Exception as e:
            print(f"⚠️ Ошибка парсинга BBOX: {e}")
            # Попытка извлечения BBOX из текста
            return self.extract_bbox_from_text(json_text)

    def extract_bbox_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Извлечение BBOX координат из текстового ответа"""
        elements = []

        # Паттерны для поиска BBOX координат
        bbox_patterns = [
            r'"bbox":\s*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]',
            r'"bbox":\s*\[(\d+\.?\d*),\s*(\d+\.?\d*),\s*(\d+\.?\d*),\s*(\d+\.?\d*)\]',
            r"\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]",
            r"bbox:\s*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]",
        ]

        # Паттерны для категорий
        category_pattern = r'"category":\s*"([^"]+)"'
        text_pattern = r'"text":\s*"([^"]*)"'

        lines = text.split("\n")
        current_element = {}

        for line in lines:
            # Поиск BBOX
            for pattern in bbox_patterns:
                bbox_match = re.search(pattern, line)
                if bbox_match:
                    coords = [int(float(x)) for x in bbox_match.groups()]
                    current_element["bbox"] = coords
                    break

            # Поиск категории
            category_match = re.search(category_pattern, line)
            if category_match:
                current_element["category"] = category_match.group(1)

            # Поиск текста
            text_match = re.search(text_pattern, line)
            if text_match:
                current_element["text"] = text_match.group(1)

            # Если найден полный элемент, добавляем его
            if "bbox" in current_element and "category" in current_element:
                elements.append(current_element.copy())
                current_element = {}

        return elements

    def get_category_color(self, category: str) -> str:
        """Получение цвета для категории"""
        # Нормализация названия категории
        category_normalized = category.strip().title()

        # Поиск точного совпадения
        if category_normalized in self.CATEGORY_COLORS:
            return self.CATEGORY_COLORS[category_normalized]

        # Поиск частичного совпадения
        for cat, color in self.CATEGORY_COLORS.items():
            if cat.lower() in category.lower() or category.lower() in cat.lower():
                return color

        # Генерация случайного цвета для неизвестной категории
        random.seed(hash(category))
        hue = random.random()
        saturation = 0.7 + random.random() * 0.3
        value = 0.8 + random.random() * 0.2
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"

    def draw_bbox_on_image(
        self,
        image: Image.Image,
        elements: List[Dict[str, Any]],
        show_labels: bool = True,
        show_confidence: bool = False,
    ) -> Image.Image:
        """Рисование BBOX на изображении"""

        # Создаем копию изображения
        img_with_boxes = image.copy()
        draw = ImageDraw.Draw(img_with_boxes)

        # Размер шрифта в зависимости от размера изображения
        font_size = max(12, min(24, min(image.size) // 50))
        font = self.get_font(font_size)

        for element in elements:
            if "bbox" not in element:
                continue

            bbox = element["bbox"]
            category = element.get("category", "Unknown")
            text = element.get("text", "")
            confidence = element.get("confidence", None)

            # Координаты BBOX
            x1, y1, x2, y2 = bbox

            # Цвет для категории
            color = self.get_category_color(category)

            # Рисуем прямоугольник
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

            if show_labels:
                # Подготовка текста метки
                label_parts = [category]

                if show_confidence and confidence is not None:
                    label_parts.append(f"{confidence:.2f}")

                if text and len(text) > 0:
                    # Ограничиваем длину текста
                    display_text = text[:30] + "..." if len(text) > 30 else text
                    label_parts.append(f'"{display_text}"')

                label = " | ".join(label_parts)

                # Размер текста метки
                bbox_text = draw.textbbox((0, 0), label, font=font)
                text_width = bbox_text[2] - bbox_text[0]
                text_height = bbox_text[3] - bbox_text[1]

                # Позиция метки (над BBOX)
                label_x = x1
                label_y = max(0, y1 - text_height - 5)

                # Фон для метки
                draw.rectangle(
                    [
                        label_x,
                        label_y,
                        label_x + text_width + 4,
                        label_y + text_height + 4,
                    ],
                    fill=color,
                    outline=color,
                )

                # Текст метки
                draw.text((label_x + 2, label_y + 2), label, fill="white", font=font)

        return img_with_boxes

    def create_legend(
        self, elements: List[Dict[str, Any]], image_width: int = 300
    ) -> Image.Image:
        """Создание легенды с категориями и цветами"""

        # Получаем уникальные категории
        categories = list(
            set(element.get("category", "Unknown") for element in elements)
        )
        categories.sort()

        if not categories:
            return None

        # Параметры легенды
        font_size = 14
        font = self.get_font(font_size)
        line_height = 25
        padding = 10
        color_box_size = 15

        # Размеры легенды
        legend_height = len(categories) * line_height + padding * 2
        legend_width = image_width

        # Создаем изображение легенды
        legend_img = Image.new("RGB", (legend_width, legend_height), "white")
        draw = ImageDraw.Draw(legend_img)

        # Заголовок
        draw.text((padding, padding), "Обнаруженные элементы:", fill="black", font=font)

        # Рисуем категории
        y_offset = padding + line_height
        for category in categories:
            color = self.get_category_color(category)

            # Цветной квадрат
            draw.rectangle(
                [
                    padding,
                    y_offset,
                    padding + color_box_size,
                    y_offset + color_box_size,
                ],
                fill=color,
                outline="black",
            )

            # Название категории
            draw.text(
                (padding + color_box_size + 10, y_offset),
                category,
                fill="black",
                font=font,
            )

            y_offset += line_height

        return legend_img

    def process_dots_ocr_response(
        self,
        image: Image.Image,
        response_text: str,
        show_labels: bool = True,
        show_confidence: bool = False,
        create_legend_img: bool = True,
    ) -> Tuple[Image.Image, Optional[Image.Image], List[Dict[str, Any]]]:
        """Полная обработка ответа dots.ocr с визуализацией"""

        # Парсинг элементов из ответа
        elements = self.parse_bbox_from_json(response_text)

        if not elements:
            print("⚠️ Не найдено элементов с BBOX координатами")
            return image, None, []

        print(f"✅ Найдено {len(elements)} элементов с BBOX координатами")

        # Рисование BBOX на изображении
        image_with_boxes = self.draw_bbox_on_image(
            image, elements, show_labels, show_confidence
        )

        # Создание легенды
        legend_img = None
        if create_legend_img:
            legend_img = self.create_legend(elements, image.width)

        return image_with_boxes, legend_img, elements

    def get_statistics(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Получение статистики по обнаруженным элементам"""

        if not elements:
            return {}

        # Подсчет по категориям
        category_counts = {}
        total_area = 0

        for element in elements:
            category = element.get("category", "Unknown")
            category_counts[category] = category_counts.get(category, 0) + 1

            # Расчет площади BBOX
            if "bbox" in element:
                x1, y1, x2, y2 = element["bbox"]
                area = (x2 - x1) * (y2 - y1)
                total_area += area

        return {
            "total_elements": len(elements),
            "categories": category_counts,
            "total_bbox_area": total_area,
            "unique_categories": len(category_counts),
        }


def test_bbox_visualizer():
    """Тестирование BBoxVisualizer"""

    # Пример JSON ответа dots.ocr
    sample_response = """
    [
        {
            "bbox": [100, 50, 400, 100],
            "category": "Title",
            "text": "Заголовок документа"
        },
        {
            "bbox": [50, 120, 450, 200],
            "category": "Text",
            "text": "Основной текст документа с важной информацией"
        },
        {
            "bbox": [100, 220, 350, 320],
            "category": "Table",
            "text": "<table><tr><td>Ячейка 1</td><td>Ячейка 2</td></tr></table>"
        },
        {
            "bbox": [400, 50, 450, 100],
            "category": "Picture",
            "text": ""
        }
    ]
    """

    # Создание тестового изображения
    test_image = Image.new("RGB", (500, 400), "white")
    draw = ImageDraw.Draw(test_image)

    # Добавляем некоторый контент
    draw.text((110, 60), "Заголовок документа", fill="black")
    draw.text((60, 130), "Основной текст документа", fill="black")
    draw.rectangle([100, 220, 350, 320], outline="gray")
    draw.rectangle([400, 50, 450, 100], fill="lightblue")

    # Тестирование визуализатора
    visualizer = BBoxVisualizer()

    # Обработка ответа
    image_with_boxes, legend_img, elements = visualizer.process_dots_ocr_response(
        test_image, sample_response, show_labels=True, create_legend_img=True
    )

    # Сохранение результатов
    image_with_boxes.save("test_bbox_visualization.png")
    if legend_img:
        legend_img.save("test_bbox_legend.png")

    # Статистика
    stats = visualizer.get_statistics(elements)
    print("📊 Статистика обнаружения:")
    print(f"   Всего элементов: {stats['total_elements']}")
    print(f"   Уникальных категорий: {stats['unique_categories']}")
    print(f"   Категории: {stats['categories']}")

    print("✅ Тест завершен. Файлы сохранены:")
    print("   - test_bbox_visualization.png")
    print("   - test_bbox_legend.png")


if __name__ == "__main__":
    test_bbox_visualizer()
