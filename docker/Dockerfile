FROM python:3.10-slim

LABEL maintainer="OlegKarenkikh"
LABEL description="ChatVLMLLM - Vision Language Models for Document OCR"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip

# Install PyTorch with CUDA 12.1 support
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install flash-attn using pre-built wheel (no CUDA dev toolkit required)
RUN pip install --no-cache-dir flash-attn --no-build-isolation

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p models utils ui docs examples tests

# Create non-root user and transfer ownership
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

# Set HuggingFace cache directory for non-root user
ENV HF_HOME=/home/appuser/.cache/huggingface

USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8501/ || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
