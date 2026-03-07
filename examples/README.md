# Example Documents

This directory contains example documents for testing the OCR and VLM capabilities.

## Directory Structure

```
examples/
├── passports/       # Passport document examples
├── invoices/        # Invoice and bill examples
├── receipts/        # Receipt examples
├── forms/           # Form examples
└── mixed/           # Mixed document types
```

## Adding Examples

### Guidelines

1. **Privacy**: Use only synthetic or public domain documents
2. **Quality**: Provide both high and low quality samples
3. **Variety**: Include different layouts, fonts, and languages
4. **Format**: Save as JPG or PNG
5. **Naming**: Use descriptive names (e.g., `passport_us_sample.jpg`)

### Sample Documents

For testing, you can:

1. Create synthetic documents using tools like:
   - Faker (Python library)
   - Online document generators
   - Design tools (Figma, Canva)

2. Use public datasets:
   - RVL-CDIP (document classification)
   - FUNSD (form understanding)
   - SROIE (receipt OCR)

3. Generate your own test documents

## Example Use Cases

### Passport OCR
```python
from PIL import Image
from models import ModelLoader

model = ModelLoader.load_model("qwen3_vl_2b")
image = Image.open("examples/passports/sample_passport.jpg")
result = model.process_image(image)
print(result)
```

### Invoice Field Extraction
```python
from PIL import Image
from models import ModelLoader
from utils.field_parser import FieldParser

model = ModelLoader.load_model("qwen3_vl_2b")
image = Image.open("examples/invoices/sample_invoice.jpg")
text = model.process_image(image)
fields = FieldParser.parse_invoice(text)
print(fields)
```

## Benchmark Results

Results from processing example documents will be documented here.

| Document Type | Model | Accuracy | Speed |
|---------------|-------|----------|-------|
| Passport | Qwen3-VL-2B | TBD | TBD |
| Invoice | Qwen3-VL-2B | TBD | TBD |
| Receipt | Qwen3-VL-2B | TBD | TBD |

## Contributing Examples

If you have interesting example documents (ensuring privacy compliance):

1. Fork the repository
2. Add your examples to appropriate directory
3. Update this README with description
4. Submit a pull request

## Legal Notice

All example documents must be:
- Non-confidential
- Synthetic or anonymized
- Properly licensed
- Free from personal information

Do not upload real identity documents or sensitive information.