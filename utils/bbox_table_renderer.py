#!/usr/bin/env python3
"""
Утилита для рендеринга BBOX результатов в виде HTML таблицы
"""

import html
from typing import List, Dict, Any

class BBoxTableRenderer:
    """Класс для создания HTML таблиц с BBOX результатами"""
    
    # Цвета категорий (синхронизированы с BBoxVisualizer)
    CATEGORY_COLORS = {
        'Text': '#FF6B6B',
        'Title': '#4ECDC4',
        'Table': '#45B7D1',
        'Picture': '#96CEB4',
        'Formula': '#FFEAA7',
        'Caption': '#DDA0DD',
        'Footnote': '#F0A500',
        'List-item': '#FF7675',
        'Page-header': '#74B9FF',
        'Page-footer': '#A29BFE',
        'Section-header': '#FD79A8',
        'Signature': '#00B894',
        'Stamp': '#E17055',
        'Logo': '#6C5CE7',
        'Barcode': '#FDCB6E',
        'QR-code': '#E84393'
    }
    
    def get_category_color(self, category: str) -> str:
        """Получение цвета для категории"""
        category_normalized = category.strip().title()
        return self.CATEGORY_COLORS.get(category_normalized, '#999999')
    
    def render_elements_table(self, elements: List[Dict[str, Any]]) -> str:
        """Создание HTML таблицы с элементами"""
        
        if not elements:
            return "<p>Нет элементов для отображения</p>"
        
        html = """
        <style>
            .bbox-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .bbox-table thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .bbox-table th {
                padding: 12px 15px;
                text-align: left;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 0.5px;
            }
            .bbox-table tbody tr {
                border-bottom: 1px solid #e0e0e0;
                transition: background-color 0.2s;
            }
            .bbox-table tbody tr:hover {
                background-color: #f5f5f5;
            }
            .bbox-table tbody tr:last-child {
                border-bottom: 2px solid #667eea;
            }
            .bbox-table td {
                padding: 10px 15px;
                font-size: 14px;
            }
            .category-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 11px;
                color: white;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .bbox-coords {
                font-family: 'Courier New', monospace;
                background-color: #f0f0f0;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                color: #333;
            }
            .element-text {
                max-width: 300px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                color: #555;
            }
            .element-number {
                font-weight: 700;
                color: #667eea;
                font-size: 16px;
            }
        </style>
        
        <table class="bbox-table">
            <thead>
                <tr>
                    <th style="width: 50px;">#</th>
                    <th style="width: 150px;">Категория</th>
                    <th style="width: 200px;">BBOX координаты</th>
                    <th>Текст</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for i, element in enumerate(elements, 1):
            bbox = element.get('bbox', [0, 0, 0, 0])
            category = element.get('category', 'Unknown')
            text = element.get('text', '')
            
            # Цвет для категории
            color = self.get_category_color(category)
            
            # Форматирование BBOX
            bbox_str = f"[{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}]"
            
            # Ограничение длины текста
            display_text = text[:100] + "..." if len(text) > 100 else text
            display_text = display_text.replace('\n', ' ').replace('\r', '')
            
            _category = html.escape(str(category))
            _bbox_str = html.escape(str(bbox_str))
            _display_text = html.escape(str(display_text))
            _title_text = html.escape(str(text))
            html += f"""
                <tr>
                    <td class="element-number">{i}</td>
                    <td>
                        <span class="category-badge" style="background-color: {color};">
                            {_category}
                        </span>
                    </td>
                    <td>
                        <code class="bbox-coords">{_bbox_str}</code>
                    </td>
                    <td class="element-text" title="{_title_text}">{_display_text}</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def render_legend(self, elements: List[Dict[str, Any]]) -> str:
        """Создание HTML легенды с категориями"""
        
        if not elements:
            return ""
        
        # Получаем уникальные категории
        categories = {}
        for element in elements:
            category = element.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
        
        html = """
        <style>
            .legend-container {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin: 15px 0;
                padding: 15px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 8px;
            }
            .legend-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                background: white;
                border-radius: 6px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }
            .legend-item:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .legend-color {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            .legend-label {
                font-weight: 600;
                color: #333;
                font-size: 13px;
            }
            .legend-count {
                background-color: #667eea;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 700;
            }
        </style>
        
        <div class="legend-container">
        """
        
        for category, count in sorted(categories.items()):
            color = self.get_category_color(category)
            _cat = html.escape(str(category))
            _cnt = html.escape(str(count))
            html += f"""
                <div class="legend-item">
                    <div class="legend-color" style="background-color: {color};"></div>
                    <span class="legend-label">{_cat}</span>
                    <span class="legend-count">{_cnt}</span>
                </div>
            """
        
        html += """
        </div>
        """
        
        return html
    
    def render_statistics(self, elements: List[Dict[str, Any]]) -> str:
        """Создание HTML блока со статистикой"""
        
        if not elements:
            return ""
        
        # Подсчет статистики
        categories = {}
        total_area = 0
        
        for element in elements:
            category = element.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
            
            bbox = element.get('bbox', [0, 0, 0, 0])
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            total_area += area
        
        html = f"""
        <style>
            .stats-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
                transition: transform 0.2s;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }}
            .stat-value {{
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 5px;
            }}
            .stat-label {{
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                opacity: 0.9;
            }}
        </style>
        
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-value">{len(elements)}</div>
                <div class="stat-label">Всего элементов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(categories)}</div>
                <div class="stat-label">Категорий</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_area:,}</div>
                <div class="stat-label">Общая площадь</div>
            </div>
        </div>
        """
        
        return html

# Тестирование
if __name__ == "__main__":
    # Пример данных
    sample_elements = [
        {"bbox": [80, 28, 220, 115], "category": "Picture"},
        {"bbox": [309, 52, 873, 104], "category": "Section-header", "text": "ВОДИТЕЛЬСКОЕ УДОСТОВЕРЕНИЕ"},
        {"bbox": [333, 129, 575, 181], "category": "List-item", "text": "1. ВАКАРИНЦЕВ VAKARINTSEV"},
        {"bbox": [331, 184, 665, 237], "category": "List-item", "text": "2. АНДРЕЙ ПАВЛОВИЧ ANDREY PAVLOVICH"},
    ]
    
    renderer = BBoxTableRenderer()
    
    print("=== HTML Статистика ===")
    print(renderer.render_statistics(sample_elements))
    
    print("\n=== HTML Легенда ===")
    print(renderer.render_legend(sample_elements))
    
    print("\n=== HTML Таблица ===")
    print(renderer.render_elements_table(sample_elements))
