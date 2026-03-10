# GPU-enabled image with CUDA
FROM nvidia/cuda:12.6.0-devel-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git wget curl \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && python3.11 -m pip install --upgrade pip

COPY requirements.txt .

RUN python3.11 -m pip install --no-cache-dir torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu126

RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501 8000

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python3.11", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
