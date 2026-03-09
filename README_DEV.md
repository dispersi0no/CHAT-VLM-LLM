# Developer Guide

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- CUDA-capable GPU (optional, but recommended)
- 16GB+ RAM

### Quick Setup

```bash
# Clone repository
git clone https://github.com/dispersi0no/CHAT-VLM-LLM.git
cd CHAT-VLM-LLM

# Run automated setup
bash scripts/setup.sh

# Check environment
python scripts/check_setup.py
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p logs results examples

# Copy environment template
cp .env.example .env
```

## Project Structure

```
CHAT-VLM-LLM/
├── app.py                 # Main Streamlit application
├── api.py                 # FastAPI REST API (port 8001)
├── config.yaml            # Model configuration (transformers + vllm)
├── requirements.txt       # Python dependencies (pinned versions)
│
├── models/               # Model integration modules
│   ├── __init__.py       # Public exports
│   ├── base_model.py     # Abstract base class
│   ├── model_loader.py   # Model factory
│   ├── qwen3_vl.py       # Qwen3-VL implementation
│   ├── qwen_vl.py        # Qwen2-VL implementation
│   ├── got_ocr.py        # GOT-OCR implementation
│   ├── dots_ocr.py       # dots.ocr implementation
│   ├── dots_ocr_final.py # dots.ocr final variant
│   └── experimental/     # Experimental models
│
├── utils/                # Utility modules
│   ├── image_processor.py    # Image preprocessing
│   ├── text_extractor.py     # Text extraction
│   ├── field_parser.py       # Field parsing
│   ├── markdown_renderer.py  # Markdown formatting
│   ├── logger.py            # Logging (setup_logger)
│   ├── cache.py             # JSON file cache
│   ├── export.py            # Export functions
│   └── validators.py        # Input validation
│
├── ui/                   # UI components
│   ├── styles.py         # CSS styling
│   └── components.py     # Reusable components
│
├── tests/                # Test suite
│   ├── conftest.py       # Shared fixtures, sys.path setup
│   ├── test_models.py    # Model integration tests
│   ├── test_utils.py     # Utility function tests
│   ├── test_api.py       # API endpoints, rate limiter, validators
│   └── test_cache.py     # JSON cache, @cached decorator
│
├── scripts/              # Utility scripts
│   ├── setup.sh         # Setup script
│   ├── download_models.py
│   ├── check_setup.py   # Environment checker
│   ├── cleanup.py       # Cleanup utility
│   └── run_tests.sh
│
├── docs/                 # Documentation
│   ├── api_guide.md      # REST API reference
│   ├── architecture.md   # System architecture
│   ├── gpu_requirements.md # GPU/VRAM guide
│   ├── models.md         # Model catalog
│   ├── model_cache_guide.md
│   └── qwen3_vl_guide.md
│
├── examples/             # Example documents for testing
├── notebooks/            # Jupyter notebooks

├── Dockerfile            # Full image (Streamlit + FastAPI, CUDA cu126)
├── Dockerfile.light      # Lightweight image without GPU deps
├── docker-compose.yml    # Standard stack (Streamlit + Nginx)
├── docker-compose-vllm.yml # vLLM stack (per-model containers)
├── nginx.conf            # Reverse proxy config
│
├── start_system.py       # System launcher
├── stop_system.py        # System shutdown
├── single_container_manager.py
├── vllm_streamlit_adapter.py
│
├── .github/workflows/ci.yml  # CI pipeline (lint + tests)
├── .dockerignore
├── .gitignore
└── .env.example
```

## Running the Application

### Streamlit UI

```bash
streamlit run app.py
```

### FastAPI REST API

```bash
# ВАЖНО: запускайте с --workers 1
# Несколько воркеров вызовут конфликт кешей моделей в GPU памяти
uvicorn api:app --host 0.0.0.0 --port 8001 --workers 1

# Документация: http://localhost:8001/docs
```

### Docker

```bash
# Стандартный стек (Streamlit + Nginx)
docker compose up -d

# vLLM стек (отдельные контейнеры для каждой модели)
docker compose -f docker-compose-vllm.yml up -d

# Только собрать образ
docker build -t chatvlmllm -f Dockerfile .

# Облегчённый образ без GPU
docker build -t chatvlmllm-light -f Dockerfile.light .
```

## Development Workflow

### Pre-commit hooks

The project uses pre-commit hooks to enforce code quality before each commit:

```bash
pip install pre-commit
pre-commit install
```

Hooks include:
- **Formatting**: black, isort
- **Linting**: flake8
- **Type checking**: mypy (core modules only)
- **Security**: detect-private-key
- **Quality**: debug-statements (no print/breakpoint), check-ast, check-merge-conflict

### 1. Code Style

We follow PEP 8 with black formatter:

```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy models/ utils/
```

### 2. Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=models --cov=utils --cov=api

# Run specific test file
pytest tests/test_api.py
pytest tests/test_cache.py

# Run with verbose output
pytest -v
```

Tests do NOT require GPU or model loading — they run in CI.

### 3. Adding New Models

To add a new model:

1. Create model class in `models/`:

```python
from models.base_model import BaseModel

class MyModel(BaseModel):
    def load_model(self):
        # Load your model
        pass
    
    def process_image(self, image):
        # Process image
        pass
```

2. Add configuration in `config.yaml` (under `transformers` or `vllm` section):

```yaml
transformers:
  my_model:
    name: "My Model"
    model_path: "org/model-name"
    precision: fp16
    device_map: auto
    # ... other config
```

3. Register in `ModelLoader`:

```python
MODEL_REGISTRY = {
    "my_model": MyModel,
    # ... other models
}
```

4. Write tests:

```python
def test_my_model():
    model = ModelLoader.load_model("my_model")
    # ... test model
```

### 4. Debugging

Enable debug logging:

```python
from utils import setup_logger

logger = setup_logger(level="DEBUG")
```

Or in `.env`:

```bash
LOG_LEVEL=DEBUG
```

### 5. Performance Profiling

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your code here
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

## Common Tasks

### Clean Caches

```bash
python scripts/cleanup.py
```

### Check Environment

```bash
python scripts/check_setup.py
```

### Download Models

```bash
python scripts/download_models.py
```

### Run Notebooks

```bash
jupyter notebook notebooks/
```

## Troubleshooting

### Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should point to venv

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### GPU Issues

```bash
# Check CUDA
nvidia-smi

# Check PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

### Memory Issues

```bash
# Use smaller model
# Set in config.yaml or .env:
DEFAULT_MODEL=qwen_vl_2b  # instead of 7b

# Enable memory optimization
OPTIMIZE_MEMORY=true
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Pull Request Checklist

- [ ] Code follows style guide (black + flake8)
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Changelog updated
- [ ] Tests passing
- [ ] No merge conflicts

## Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [Project Wiki](https://github.com/dispersi0no/CHAT-VLM-LLM/wiki)

## License

MIT License - see [LICENSE](LICENSE) file
