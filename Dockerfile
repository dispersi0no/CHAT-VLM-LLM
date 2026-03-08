# GPU-enabled image with CUDA
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies and Python
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    wget \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

# Copy requirements first for better caching
COPY requirements.txt .

# Install PyTorch with CUDA 12.1 support
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install flash-attn using pre-built wheel (no CUDA dev toolkit required)
RUN pip install --no-cache-dir flash-attn --no-build-isolation

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create non-root user and transfer ownership
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

# Set HuggingFace cache directory for non-root user
ENV HF_HOME=/home/appuser/.cache/huggingface

USER appuser

# Expose ports
EXPOSE 8501 8000

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
