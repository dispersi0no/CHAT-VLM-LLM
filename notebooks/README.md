# Jupyter Notebooks

Interactive notebooks for exploring and testing the ChatVLMLLM models.

## Available Notebooks

### 1. Model Exploration (`01_model_exploration.ipynb`)

Introductory notebook that demonstrates:
- Loading and using different models
- Image preprocessing
- Text extraction and post-processing
- Entity extraction
- Interactive chat with VLM models
- Performance comparison

**Use this notebook to:**
- Get started with the models
- Test on single documents
- Experiment with different approaches
- Learn the API

### 2. Batch Processing (`02_batch_processing.ipynb`)

Production-oriented notebook for:
- Processing multiple documents
- Collecting and analyzing results
- Exporting structured data
- Performance analysis
- Statistical evaluation

**Use this notebook to:**
- Process document batches
- Benchmark model performance
- Generate datasets for evaluation
- Production workflows

## Setup

### Install Jupyter

```bash
pip install jupyter notebook ipywidgets matplotlib
```

### Launch Notebook Server

```bash
# From project root
jupyter notebook notebooks/
```

### Required Dependencies

All notebooks require the project dependencies:
```bash
pip install -r requirements.txt
```

Additional notebook-specific dependencies:
```bash
pip install tqdm matplotlib seaborn
```

## Usage Tips

### GPU Memory

- Notebooks may use significant GPU memory
- Restart kernel if switching between large models
- Use `ModelLoader.unload_model()` to free memory

### Data Organization

Organize your test data:
```
examples/
├── invoices/
│   ├── invoice1.jpg
│   └── invoice2.jpg
├── passports/
│   └── passport1.jpg
└── receipts/
    └── receipt1.jpg
```

### Saving Results

Notebooks create a `results/` directory for outputs:
- Processed images
- Extracted text
- CSV/JSON exports
- Visualizations

## Creating New Notebooks

When creating new notebooks:

1. Add project to path:
```python
import sys
sys.path.append('..')
```

2. Import project modules:
```python
from models import ModelLoader
from utils import ImageProcessor
```

3. Document your workflow
4. Include error handling
5. Save results for reproducibility

## Troubleshooting

### Import Errors

Ensure project root is in path:
```python
import sys
import os
sys.path.append(os.path.abspath('..'))
```

### CUDA Out of Memory

```python
import torch
torch.cuda.empty_cache()
ModelLoader.unload_all()
```

### Slow Inference

- Use smaller models (Qwen2-VL-2B vs 7B)
- Enable Flash Attention if available
- Process images in batches
- Reduce image size during preprocessing

## Contributing

Share your notebooks!

1. Create useful analysis notebooks
2. Document your experiments
3. Share interesting findings
4. Submit PR with your notebook

## Examples

### Quick OCR

```python
from PIL import Image
from models import ModelLoader

model = ModelLoader.load_model('dots_ocr')
image = Image.open('document.jpg')
text = model.process_image(image)
print(text)
```

### Interactive Chat

```python
model = ModelLoader.load_model('qwen3_vl_2b')
response = model.chat(image, "What's in this document?")
print(response)
```

### Batch Processing

```python
from pathlib import Path
images = Path('examples/').glob('*.jpg')

for img_path in images:
    img = Image.open(img_path)
    result = model.process_image(img)
    print(f"{img_path.name}: {result[:100]}...")
```