#!/usr/bin/env python3
"""
Адаптер для интеграции vLLM API с Streamlit интерфейсом
Включает управление памятью и автоматическое переключение контейнеров
ПРИНЦИП: Только один активный контейнер одновременно
"""

import requests
import base64
import time
import streamlit as st
from PIL import Image
import io
from typing import Optional, Dict, Any, List
from single_container_manager import SingleContainerManager

class VLLMStreamlitAdapter:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.available_models = []
        
        # Инициализация менеджера одиночных контейнеров
        self.container_manager = SingleContainerManager()
        
        # Маппинг моделей на порты для множественных контейнеров
        self.model_endpoints = {
            "rednote-hilab/dots.ocr": "http://localhost:8000",
            "Qwen/Qwen2-VL-2B-Instruct": "http://localhost:8001", 
            "Qwen/Qwen3-VL-2B-Instruct": "http://localhost:8004",
            "microsoft/Phi-3.5-vision-instruct": "http://localhost:8002",
            "Qwen/Qwen2-VL-7B-Instruct": "http://localhost:8003"
        }
        
        # Приоритеты моделей для отображения
        self.model_priorities = {
            "rednote-hilab/dots.ocr": 1,
            "Qwen/Qwen3-VL-2B-Instruct": 2,
            "Qwen/Qwen2-VL-2B-Instruct": 3,
            "microsoft/Phi-3.5-vision-instruct": 4,
            "Qwen/Qwen2-VL-7B-Instruct": 5
        }
        
        self.check_all_connections()
    
    def check_all_connections(self) -> bool:
        """Проверка подключения к активному vLLM серверу"""
        self.available_models = []
        self.model_limits = {}
        self.healthy_endpoints = {}
        
        # Получаем активную модель от менеджера контейнеров
        active_model_key = self.container_manager.get_active_model()
        
        if not active_model_key:
            st.warning("⚠️ Нет активной модели. Выберите модель для активации.")
            return False
        
        # Получаем конфигурацию активной модели
        active_config = self.container_manager.models_config.get(active_model_key)
        if not active_config:
            st.error(f"❌ Конфигурация модели {active_model_key} не найдена")
            return False
        
        model_path = active_config["model_path"]
        endpoint = f"http://localhost:{active_config['port']}"
        
        try:
            # Проверяем health
            response = requests.get(f"{endpoint}/health", timeout=5)
            if response.status_code == 200:
                # Проверяем models endpoint
                models_response = requests.get(f"{endpoint}/v1/models", timeout=5)
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    for model in models_data.get("data", []):
                        if model["id"] == model_path:
                            self.available_models.append(model_path)
                            self.model_limits[model_path] = model.get("max_model_len", 1024)
                            self.healthy_endpoints[model_path] = endpoint
                            
                            st.success(f"✅ {active_config['display_name']} активна и готова")
                            return True
                
                st.warning(f"⚠️ Модель {model_path} не найдена в API")
                return False
            else:
                st.warning(f"⚠️ {active_config['display_name']} недоступна (health check failed)")
                return False
                
        except Exception as e:
            st.warning(f"⚠️ {active_config['display_name']} недоступна: {str(e)[:50]}...")
            return False
    
    def get_endpoint_for_model(self, model_name: str) -> str:
        """Получение endpoint для конкретной модели"""
        return self.healthy_endpoints.get(model_name, self.base_url)
    
    def ensure_model_available(self, model_name: str) -> bool:
        """Обеспечение доступности модели через менеджер контейнеров"""
        
        # Проверяем, активна ли уже нужная модель
        if model_name in self.healthy_endpoints:
            return True
        
        # Находим ключ модели в конфигурации менеджера
        target_model_key = None
        for model_key, config in self.container_manager.models_config.items():
            if config["model_path"] == model_name:
                target_model_key = model_key
                break
        
        if not target_model_key:
            st.error(f"❌ Модель {model_name} не найдена в конфигурации")
            return False
        
        # Переключаемся на нужную модель
        st.info(f"🔄 Переключение на {model_name.split('/')[-1]}...")
        success, message = self.container_manager.start_single_container(target_model_key)
        
        if success:
            # Обновляем список доступных endpoints
            time.sleep(3)  # Даем время на стабилизацию
            self.check_all_connections()
            return model_name in self.healthy_endpoints
        else:
            st.error(f"❌ Не удалось активировать модель {model_name}: {message}")
            return False
    
    def get_recommended_models(self) -> List[str]:
        """Получение рекомендуемых моделей в порядке приоритета"""
        # Сортируем доступные модели по приоритету
        available_sorted = sorted(
            self.available_models,
            key=lambda x: self.model_priorities.get(x, 999)
        )
        return available_sorted
    
    def check_connection(self) -> bool:
        """Проверка подключения к vLLM серверу (legacy метод)"""
        return self.check_all_connections()
    
    def get_available_models(self) -> list:
        """Получение списка доступных моделей"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                self.available_models = []
                self.model_limits = {}
                
                for model in models_data.get("data", []):
                    model_id = model["id"]
                    max_tokens = model.get("max_model_len", 1024)
                    
                    self.available_models.append(model_id)
                    self.model_limits[model_id] = max_tokens
                
                return self.available_models
        except Exception as e:
            st.error(f"❌ Ошибка получения моделей: {e}")
        return []
    
    def get_model_max_tokens(self, model_id: str) -> int:
        """Получение максимального количества токенов для модели"""
        return getattr(self, 'model_limits', {}).get(model_id, 1024)
    
    def chat_with_image(self, image: Image.Image, prompt: str, 
                       model: str = "rednote-hilab/dots.ocr") -> Optional[Dict[str, Any]]:
        """Чат с изображением через vLLM API"""
        return self.process_image(image, prompt, model)
    
    def process_image(self, image: Image.Image, prompt: str = "Extract all text from this image", 
                     model: str = "rednote-hilab/dots.ocr", max_tokens: int = 4096) -> Optional[Dict[str, Any]]:
        """Обработка изображения через vLLM API с автоматическим управлением контейнерами"""
        
        # Проверяем и обеспечиваем доступность модели
        if not self.ensure_model_available(model):
            return {
                "success": False,
                "error": f"Модель {model} недоступна",
                "text": "",
                "processing_time": 0
            }
        
        # Получаем правильный endpoint для модели
        endpoint = self.get_endpoint_for_model(model)
        
        # Проверяем лимит токенов для модели
        model_max_tokens = self.get_model_max_tokens(model)
        
        # УЛУЧШЕНИЕ: Более детальная проверка токенов
        if max_tokens > model_max_tokens:
            st.warning(f"⚠️ Запрошено {max_tokens} токенов, но модель {model} поддерживает максимум {model_max_tokens}")
            max_tokens = model_max_tokens
        
        # Дополнительная проверка: оставляем место для входных токенов
        estimated_input_tokens = len(prompt.split()) * 1.3 + 200  # Примерная оценка: промпт + изображение
        if max_tokens + estimated_input_tokens > model_max_tokens:
            adjusted_tokens = max(100, model_max_tokens - int(estimated_input_tokens))
            st.info(f"🔧 Автоматически скорректированы токены: {max_tokens} → {adjusted_tokens} (резерв для входных токенов)")
            max_tokens = adjusted_tokens
        
        # Конвертация изображения в base64
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Подготовка запроса
        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]
            }],
            "max_tokens": max_tokens,  # Ограниченное количество токенов
            "temperature": 0.1
        }
        
        try:
            # Отправка запроса к правильному endpoint
            start_time = time.time()
            
            model_display_name = model.split('/')[-1]
            with st.spinner(f"🔄 Обработка изображения через {model_display_name} (макс. {max_tokens} токенов)..."):
                response = requests.post(
                    f"{endpoint}/v1/chat/completions",
                    json=payload,
                    timeout=120
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                return {
                    "success": True,
                    "text": content,
                    "processing_time": processing_time,
                    "model": model,
                    "model_display_name": model_display_name,
                    "endpoint": endpoint,
                    "mode": "vLLM",
                    "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                    "max_tokens_limit": model_max_tokens,
                    "actual_max_tokens": max_tokens
                }
            else:
                error_text = response.text
                st.error(f"❌ API ошибка: {response.status_code}")
                
                # Специальная обработка ошибок валидации токенов
                if "max_tokens" in error_text and "exceeds" in error_text:
                    st.error("🚨 **ОШИБКА ЛИМИТА ТОКЕНОВ**")
                    st.error(f"Запрошено токенов: {max_tokens}")
                    st.error(f"Лимит модели: {model_max_tokens}")
                    st.info("💡 **Решение:** Уменьшите количество токенов в настройках или используйте автоматическую коррекцию")
                
                st.error(f"Ответ сервера: {error_text}")
                return {
                    "success": False,
                    "error": f"API ошибка: {response.status_code}",
                    "text": "",
                    "processing_time": processing_time
                }
                
        except Exception as e:
            st.error(f"❌ Ошибка обработки через {endpoint}: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "processing_time": 0
            }
    
    def get_server_status(self) -> Dict[str, Any]:
        """Получение статуса всех серверов"""
        healthy_count = len(self.healthy_endpoints)
        total_count = len(self.model_endpoints)
        
        return {
            "status": "healthy" if healthy_count > 0 else "error",
            "healthy_endpoints": healthy_count,
            "total_endpoints": total_count,
            "available_models": self.available_models,
            "model_limits": getattr(self, 'model_limits', {}),
            "endpoints": self.healthy_endpoints
        }

def create_vllm_interface():
    """Создание интерфейса для работы с vLLM"""
    st.header("🚀 vLLM Режим")
    
    # Инициализация адаптера
    if "vllm_adapter" not in st.session_state:
        st.session_state.vllm_adapter = VLLMStreamlitAdapter()
    
    adapter = st.session_state.vllm_adapter
    
    # Статус сервера
    status = adapter.get_server_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if status["status"] == "healthy":
            st.success(f"✅ vLLM Серверы ({status['healthy_endpoints']}/{status['total_endpoints']})")
        else:
            st.error("❌ vLLM Недоступен")
    
    with col2:
        st.info(f"🤖 Моделей: {len(status['available_models'])}")
    
    with col3:
        if status.get("endpoints"):
            st.info(f"🌐 Активных портов: {len(status['endpoints'])}")
    
    if status["status"] != "healthy":
        st.error("❌ vLLM серверы недоступны. Запустите контейнеры:")
        st.code("docker-compose -f docker-compose-vllm.yml up -d")
        return
    
    # Выбор модели с улучшенным интерфейсом
    if adapter.available_models:
        recommended_models = adapter.get_recommended_models()
        
        # Отображаем статус памяти
        memory_status = adapter.memory_manager.get_memory_status()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_model = st.selectbox(
                "🤖 Выберите модель",
                recommended_models,
                help="Модели отсортированы по приоритету. Система автоматически управляет памятью."
            )
        
        with col2:
            st.metric(
                "GPU память", 
                f"{memory_status['current_memory_gb']:.1f}/{memory_status['max_memory_gb']} ГБ",
                f"{memory_status['memory_usage_percent']:.1f}%"
            )
        
        # Информация о выбранной модели
        if selected_model in adapter.healthy_endpoints:
            st.success(f"✅ {selected_model.split('/')[-1]} активна и готова к работе")
        else:
            st.warning(f"⚠️ {selected_model.split('/')[-1]} будет активирована автоматически при обработке")
            
            if st.button("🚀 Активировать модель сейчас"):
                with st.spinner("Активация модели..."):
                    success = adapter.ensure_model_available(selected_model)
                    if success:
                        st.success("✅ Модель активирована!")
                        st.rerun()
                    else:
                        st.error("❌ Ошибка активации модели")
    else:
        st.error("❌ Нет доступных моделей")
        return
    
    # Настройки промпта
    st.subheader("📝 Настройки обработки")
    
    prompt_type = st.selectbox(
        "Тип задачи",
        [
            "Extract all text from this image",
            "Describe what you see in this image",
            "Extract structured data from this document",
            "Identify and extract key information",
            "Custom prompt"
        ]
    )
    
    if prompt_type == "Custom prompt":
        custom_prompt = st.text_area(
            "Введите свой промпт",
            value="Extract all text from this image",
            help="Опишите, что должна сделать модель с изображением"
        )
        prompt = custom_prompt
    else:
        prompt = prompt_type
    
    # Загрузка изображения
    st.subheader("📷 Загрузка изображения")
    
    uploaded_file = st.file_uploader(
        "Выберите изображение",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        help="Поддерживаемые форматы: PNG, JPG, JPEG, BMP, TIFF"
    )
    
    if uploaded_file is not None:
        # Отображение изображения
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image, caption="Загруженное изображение", use_column_width=True)
            st.info(f"📏 Размер: {image.size[0]}x{image.size[1]}")
        
        with col2:
            if st.button("🚀 Обработать изображение", type="primary", use_container_width=True):
                result = adapter.process_image(image, prompt, selected_model)
                
                if result and result["success"]:
                    st.success("✅ Обработка завершена!")
                    
                    # Результат
                    st.subheader("📄 Результат OCR")
                    st.text_area(
                        "Извлеченный текст",
                        value=result["text"],
                        height=200,
                        help="Результат обработки изображения"
                    )
                    
                    # Метрики
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("⏱️ Время", f"{result['processing_time']:.1f} сек")
                    
                    with col2:
                        st.metric("🤖 Модель", result.get("model_display_name", result["model"].split("/")[-1]))
                    
                    with col3:
                        st.metric("🔧 Режим", result["mode"])
                    
                    with col4:
                        st.metric("🔢 Токенов", result.get("tokens_used", 0))
                    
                    # Дополнительная информация
                    with st.expander("📊 Подробная информация"):
                        st.json({
                            "model": result["model"],
                            "processing_time": result["processing_time"],
                            "tokens_used": result.get("tokens_used", 0),
                            "mode": result["mode"],
                            "prompt": prompt
                        })
                    
                    # Кнопки экспорта
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📋 Копировать текст"):
                            st.write("Текст скопирован в буфер обмена!")
                    
                    with col2:
                        # Экспорт в JSON
                        export_data = {
                            "text": result["text"],
                            "model": result["model"],
                            "processing_time": result["processing_time"],
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        st.download_button(
                            "💾 Скачать JSON",
                            data=str(export_data),
                            file_name=f"ocr_result_{int(time.time())}.json",
                            mime="application/json"
                        )

if __name__ == "__main__":
    create_vllm_interface()