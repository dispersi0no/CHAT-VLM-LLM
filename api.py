"""ChatVLMLLM FastAPI REST API.

REST API для Vision-Language Models OCR и чата.

Использование:
    uvicorn api:app --host 0.0.0.0 --port 8001 --reload
    
Документация: http://localhost:8001/docs
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from PIL import Image
from collections import defaultdict
import io
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Конфигурация безопасности
# =============================================================================

class SecurityConfig:
    """Настройки безопасности API."""
    
    # CORS настройки
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:8501,http://localhost:3000,http://127.0.0.1:8501"
    ).split(",")
    
    # Rate limiting (запросов в минуту)
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT", "60"))
    
    # Ограничения файлов
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    MAX_BATCH_SIZE: int = 10  # Максимум файлов в пакете
    
    # Разрешённые MIME-типы
    ALLOWED_MIME_TYPES: List[str] = [
        "image/jpeg",
        "image/png", 
        "image/bmp",
        "image/tiff",
        "image/webp"
    ]
    
    # Разрешённые расширения
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"]


security_config = SecurityConfig()


# =============================================================================
# Rate Limiting
# =============================================================================

class RateLimiter:
    """Простой rate limiter на основе IP."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        """Проверка, разрешён ли запрос."""
        now = time.time()
        minute_ago = now - 60
        
        # Очистка старых записей
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > minute_ago
        ]
        
        # Проверка лимита
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        # Запись нового запроса
        self.requests[client_ip].append(now)
        return True
    
    def get_remaining(self, client_ip: str) -> int:
        """Получение оставшихся запросов."""
        now = time.time()
        minute_ago = now - 60
        recent = [t for t in self.requests[client_ip] if t > minute_ago]
        return max(0, self.requests_per_minute - len(recent))


rate_limiter = RateLimiter(security_config.RATE_LIMIT_PER_MINUTE)


# =============================================================================
# Валидация файлов
# =============================================================================

def validate_file(file: UploadFile, content: bytes) -> None:
    """
    Валидация загруженного файла.
    
    Args:
        file: Объект загруженного файла
        content: Содержимое файла
        
    Raises:
        HTTPException: При ошибке валидации
    """
    # Проверка размера
    if len(content) > security_config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Файл слишком большой. Максимум: {security_config.MAX_FILE_SIZE // 1024 // 1024} MB"
        )
    
    # Проверка расширения
    if file.filename:
        ext = os.path.splitext(file.filename.lower())[1]
        if ext not in security_config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Недопустимое расширение файла. Разрешены: {', '.join(security_config.ALLOWED_EXTENSIONS)}"
            )
    
    # Проверка MIME-типа через PIL (надёжная проверка по содержимому)
    # Проверка, что файл является валидным изображением
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
        # verify() закрывает поток, поэтому повторно открываем изображение для дальнейшей обработки
        image = Image.open(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Файл не является валидным изображением: {str(e)}"
        )


async def rate_limit_check(request: Request):
    """Dependency для проверки rate limit."""
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        remaining = rate_limiter.get_remaining(client_ip)
        raise HTTPException(
            status_code=429,
            detail=f"Превышен лимит запросов. Попробуйте через минуту.",
            headers={"X-RateLimit-Remaining": str(remaining)}
        )


# =============================================================================
# FastAPI приложение
# =============================================================================

app = FastAPI(
    title="ChatVLMLLM API",
    description="REST API для Vision-Language Models OCR и чата",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS с настраиваемыми origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Remaining"]
)


# Кеш моделей
model_cache = {}


def get_model(model_name: str):
    """Загрузка и кеширование модели."""
    if model_name not in model_cache:
        try:
            from models import ModelLoader
            logger.info(f"Загрузка модели: {model_name}")
            model_cache[model_name] = ModelLoader.load_model(model_name)
            logger.info(f"Модель загружена успешно: {model_name}")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели {model_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка загрузки модели: {str(e)}")
    return model_cache[model_name]


# =============================================================================
# Эндпоинты
# =============================================================================

@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "ChatVLMLLM API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса и статуса GPU."""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_available else None
        vram_total = None
        vram_used = None
        if gpu_available:
            vram_total = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2)
            vram_used = round(torch.cuda.memory_allocated(0) / 1e9, 2)
    except:
        gpu_available = False
        gpu_name = None
        vram_total = None
        vram_used = None
    
    return {
        "status": "healthy",
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "vram_total_gb": vram_total,
        "vram_used_gb": vram_used,
        "models_loaded": len(model_cache),
        "loaded_models": list(model_cache.keys()),
        "rate_limit_per_minute": security_config.RATE_LIMIT_PER_MINUTE
    }


@app.get("/models")
async def list_models():
    """Список доступных моделей."""
    return {
        "available": [
            {"id": "got_ocr", "name": "GOT-OCR 2.0", "params": "580M", "vram_fp16": "3GB"},
            {"id": "qwen_vl_2b", "name": "Qwen2-VL 2B", "params": "2B", "vram_fp16": "4.7GB"},
            {"id": "qwen3_vl_2b", "name": "Qwen3-VL 2B", "params": "2B", "vram_fp16": "4.4GB"},
            {"id": "dots_ocr", "name": "dots.ocr", "params": "1.7B", "vram_bf16": "8GB"},
        ],
        "loaded": list(model_cache.keys())
    }


@app.post("/ocr", dependencies=[Depends(rate_limit_check)])
async def extract_text(
    request: Request,
    file: UploadFile = File(...),
    model: str = "qwen3_vl_2b",
    language: Optional[str] = None
):
    """
    Извлечение текста из изображения.
    
    Args:
        file: Файл изображения (JPG, PNG, BMP, TIFF)
        model: Модель для использования (по умолчанию: qwen3_vl_2b)
        language: Подсказка языка (опционально)
    
    Returns:
        Извлечённый текст с метаданными
    """
    try:
        # Чтение и валидация файла
        image_data = await file.read()
        validate_file(file, image_data)
        
        image = Image.open(io.BytesIO(image_data))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        model_instance = get_model(model)
        start_time = time.time()
        
        # Обработка в зависимости от типа модели
        if "qwen3" in model:
            text = model_instance.extract_text(image, language=language)
        elif "qwen" in model:
            text = model_instance.chat(image, "Extract all text from this document.")
        elif model == "dots_ocr":
            result = model_instance.parse_document(image, return_json=False)
            text = result.get('raw_text', str(result))
        else:  # GOT-OCR
            text = model_instance.process_image(image)
        
        processing_time = time.time() - start_time
        
        # Добавление заголовка с оставшимися запросами
        client_ip = request.client.host if request.client else "unknown"
        remaining = rate_limiter.get_remaining(client_ip)
        
        return JSONResponse(
            content={
                "text": text,
                "model": model,
                "processing_time": round(processing_time, 3),
                "image_size": list(image.size),
                "language": language
            },
            headers={"X-RateLimit-Remaining": str(remaining)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка OCR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", dependencies=[Depends(rate_limit_check)])
async def chat_with_image(
    request: Request,
    file: UploadFile = File(...),
    prompt: str = Form(default="Опишите это изображение"),
    model: str = Form(default="qwen3_vl_2b"),
    temperature: float = Query(default=0.7, ge=0.0, le=1.0),
    max_tokens: int = Query(default=512, ge=1, le=4096)
):
    """
    Чат с VLM моделью об изображении.
    
    Args:
        file: Файл изображения
        prompt: Вопрос пользователя
        model: Модель для использования
        temperature: Температура сэмплирования (0.0-1.0)
        max_tokens: Максимум токенов для генерации (1-4096)
    
    Returns:
        Ответ модели
    """
    try:
        # Чтение и валидация файла
        image_data = await file.read()
        validate_file(file, image_data)
        
        image = Image.open(io.BytesIO(image_data))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Санитизация промпта
        prompt = prompt.strip()[:2000]  # Ограничение длины промпта
        
        model_instance = get_model(model)
        start_time = time.time()
        
        if "qwen" in model:
            response = model_instance.chat(
                image=image,
                prompt=prompt,
                temperature=temperature,
                max_new_tokens=max_tokens
            )
        elif model == "dots_ocr":
            response = str(model_instance.process_image(image, prompt=prompt))
        else:  # GOT-OCR
            response = model_instance.process_image(image)
        
        processing_time = time.time() - start_time
        
        client_ip = request.client.host if request.client else "unknown"
        remaining = rate_limiter.get_remaining(client_ip)
        
        return JSONResponse(
            content={
                "response": response,
                "model": model,
                "processing_time": round(processing_time, 3),
                "prompt": prompt
            },
            headers={"X-RateLimit-Remaining": str(remaining)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка чата: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch/ocr", dependencies=[Depends(rate_limit_check)])
async def batch_ocr(
    request: Request,
    files: List[UploadFile] = File(...),
    model: str = "qwen3_vl_2b"
):
    """
    Пакетная обработка OCR.
    
    Args:
        files: Список файлов изображений (максимум 10)
        model: Модель для использования
    
    Returns:
        Список результатов
    """
    # Проверка количества файлов
    if len(files) > security_config.MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Слишком много файлов. Максимум: {security_config.MAX_BATCH_SIZE}"
        )
    
    results = []
    
    for file in files:
        try:
            image_data = await file.read()
            validate_file(file, image_data)
            
            image = Image.open(io.BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            model_instance = get_model(model)
            start_time = time.time()
            
            if "qwen3" in model:
                text = model_instance.extract_text(image)
            elif "qwen" in model:
                text = model_instance.chat(image, "Extract all text.")
            else:
                text = model_instance.process_image(image)
            
            processing_time = time.time() - start_time
            
            results.append({
                "filename": file.filename,
                "text": text,
                "processing_time": round(processing_time, 3),
                "status": "success"
            })
            
        except HTTPException as e:
            results.append({
                "filename": file.filename,
                "error": e.detail,
                "status": "error"
            })
        except Exception as e:
            logger.error(f"Ошибка пакетной обработки для {file.filename}: {e}")
            results.append({
                "filename": file.filename,
                "error": str(e),
                "status": "error"
            })
    
    successful = sum(1 for r in results if r["status"] == "success")
    
    client_ip = request.client.host if request.client else "unknown"
    remaining = rate_limiter.get_remaining(client_ip)
    
    return JSONResponse(
        content={
            "results": results,
            "total": len(files),
            "successful": successful,
            "failed": len(files) - successful
        },
        headers={"X-RateLimit-Remaining": str(remaining)}
    )


@app.delete("/models/{model_name}")
async def unload_model(model_name: str):
    """Выгрузка модели из памяти."""
    if model_name in model_cache:
        try:
            model = model_cache[model_name]
            if hasattr(model, 'unload'):
                model.unload()
            del model_cache[model_name]
            
            # Очистка CUDA кеша
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass
            
            logger.info(f"Модель выгружена: {model_name}")
            return {"status": "success", "message": f"Модель {model_name} выгружена"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=404, detail=f"Модель {model_name} не загружена")


# =============================================================================
# Обработчики ошибок
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Обработчик HTTP исключений."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработчик общих исключений."""
    logger.error(f"Необработанная ошибка: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера", "status_code": 500}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
