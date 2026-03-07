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
├── api.py                 # FastAPI REST API
├── config.yaml            # Model and app configuration
├── requirements.txt       # Python dependencies
│
├── models/               # Model integration modules
│   ├── base_model.py     # Abstract base class
│   ├── got_ocr.py        # GOT-OCR implementation
│   ├── qwen_vl.py        # Qwen2-VL implementation
│   ├── qwen3_vl.py       # Qwen3-VL implementation
│   ├── dots_ocr.py       # dots.ocr implementation
│   └── model_loader.py   # Model factory
│
├── utils/                # Utility modules
│   ├── image_processor.py    # Image preprocessing
│   ├── text_extractor.py     # Text extraction
│   ├── field_parser.py       # Field parsing
│   ├── markdown_renderer.py  # Markdown formatting
│   ├── logger.py            # Logging configuration
│   ├── cache.py             # Caching utilities
│   ├── export.py            # Export functions
│   └── validators.py        # Input validation
│
├── ui/                   # UI components
│   ├── styles.py         # CSS styling
│   └── components.py     # Reusable components
│
├── tests/                # Test suite
│   ├── test_models.py
│   └── test_utils.py
│
├── scripts/              # Utility scripts
│   ├── setup.sh         # Setup script
│   ├── download_models.py
│   ├── check_setup.py   # Environment checker
│   ├── cleanup.py       # Cleanup utility
│   └── run_tests.sh
│
├── docs/                 # Documentation
│   ├── api_guide.md
│   ├── architecture.md
│   ├── gpu_requirements.md
│   ├── models.md
│   ├── model_cache_guide.md
│   └── qwen3_vl_guide.md
│
├── examples/             # Example documents for testing
├── notebooks/            # Jupyter notebooks
│   ├── 01_model_exploration.ipynb
│   └── 02_batch_processing.ipynb
│
├── dots_ocr/             # dots.ocr integration module
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Development Workflow

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
pytest --cov=models --cov=utils

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v
```

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

### Build Docker Image

```bash
docker build -t chatvlmllm -f Dockerfile .
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