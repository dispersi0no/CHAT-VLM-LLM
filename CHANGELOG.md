# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Fine-tuning support
- Cloud deployment guide
- Performance benchmarks

## [0.3.0] - 2026-03-07

### Added
- **vLLM Support**
  - dots.ocr model via vLLM backend
  - Qwen2-VL / Qwen3-VL vLLM mode
  - Separate docker-compose-vllm.yml

- **FastAPI REST API** (`api.py`)
  - OCR endpoint (`POST /ocr`)
  - Chat endpoint (`POST /chat`)
  - Batch processing (`POST /batch/ocr`)
  - Model management endpoints

- **New Models**
  - dots.ocr integration (SOTA document parser, 100+ languages)
  - Qwen3-VL (2B/4B/8B) with 32-language OCR, 256K context

- **Infrastructure**
  - `.dockerignore` for optimized Docker builds
  - `start_system.py` / `stop_system.py` for system management
  - Model cache management (`utils/model_cache.py`)
  - Smart content renderer (`utils/smart_content_renderer.py`)

### Changed
- **Full Project Audit & Cleanup**
  - Removed ~370 junk files (462 → ~85 files)
  - Rewrote `.gitignore` (fixed UTF-16 null bytes)
  - Pinned all dependency versions in `requirements.txt`
  - Cleaned `models/__init__.py` — only working model exports
  - Rewrote `model_loader.py` — single clean loader, no dead imports
  - Removed dead utils modules (cuda_recovery, mode_switcher, etc.)
  - Disabled permanent emergency_mode in `config.yaml`
  - Enabled GPU optimizations (cudnn_benchmark, SDPA, tf32)
  - Fixed all documentation links (dispersi0no/CHAT-VLM-LLM)
  - Updated project structure in README, README_DEV, CONTRIBUTING
  - Fixed CI/CD — black/isort checks now report properly
  - Fixed tests to match current config.yaml structure
  - Removed unused scripts (update_blackwell_libraries.py)
  - Updated docs (architecture, api_guide, models) to reflect reality

### Removed
- ~370 temporary files (tests, fixes, debug scripts, JSON reports, backups)
- Duplicate dots_ocr model variants (9 files)
- Duplicate docker/ directory and docker-compose variants
- model_loader_emergency.py / model_loader_backup.py
- Broken Dockerfile.vllm-fixed
- Empty research_log.md
- Unused utils (cuda_recovery, optimized_generation, mode_switcher, performance_analyzer, visualizer, memory_controller)

## [0.2.0] - 2026-01-15

### Added
- **Production Utilities**
  - Colored logging system with file output (`utils/logger.py`)
  - File-based caching for model results (`utils/cache.py`)
  - Export utilities for JSON/CSV/TXT formats (`utils/export.py`)
  - Input validation and sanitization (`utils/validators.py`)
  
- **Enhanced Application**
  - Complete UI rewrite with modern design
  - Session state management for chat history
  - OCR mode with preview and settings
  - Interactive chat mode with history
  - Model comparison page
  - In-app documentation
  
- **UI Components**
  - Reusable component library (`ui/components.py`)
  - Metric cards, progress bars, model cards
  - Feature lists and code examples
  - Comparison tables and alerts
  
- **Developer Tools**
  - Environment check script (`scripts/check_setup.py`)
  - Cleanup utility (`scripts/cleanup.py`)
  - Environment configuration template (`.env.example`)
  - Developer guide (`README_DEV.md`)
  
- **Project Structure**
  - Examples directory with instructions
  - Logs directory for application logs
  - Results directory for outputs
  - Enhanced `.gitignore` for caches and logs

### Changed
- Updated `app.py` with placeholder model integration
- Improved `utils/__init__.py` with all utility exports
- Enhanced documentation with usage examples
- Better error handling throughout the application

### Fixed
- Session state initialization issues
- File upload validation
- Export functionality placeholders

## [0.1.0] - 2026-01-10

### Added
- **Project Foundation**
  - Initial project structure
  - MIT License
  - README with project overview
  - CONTRIBUTING guidelines
  
- **Model Integration Framework**
  - Abstract base model class (`models/base_model.py`)
  - GOT-OCR 2.0 integration module (`models/got_ocr.py`)
  - Qwen2-VL integration module (`models/qwen_vl.py`)
  - Model factory pattern (`models/model_loader.py`)
  
- **Utility Modules**
  - Image preprocessing pipeline (`utils/image_processor.py`)
  - Text extraction and cleaning (`utils/text_extractor.py`)
  - Field parser for structured documents (`utils/field_parser.py`)
  - Markdown rendering utilities (`utils/markdown_renderer.py`)
  
- **UI Components**
  - Modern CSS styling system (`ui/styles.py`)
  - Streamlit application template (`app.py`)
  
- **Testing**
  - Test framework setup
  - Model integration tests (`tests/test_models.py`)
  - Utility function tests (`tests/test_utils.py`)
  - Test running script (`scripts/run_tests.sh`)
  
- **Documentation**
  - Quick start guide (`QUICKSTART.md`)
  - Model documentation (`docs/models.md`)
  - Architecture documentation (`docs/architecture.md`)
  - Research log template (`docs/research_log.md`)
  - Project summary (`PROJECT_SUMMARY.md`)
  
- **Interactive Notebooks**
  - Model exploration notebook (`notebooks/01_model_exploration.ipynb`)
  - Batch processing notebook (`notebooks/02_batch_processing.ipynb`)
  - Notebook usage guide (`notebooks/README.md`)
  
- **Docker Support**
  - Dockerfile for containerization (`docker/Dockerfile`)
  - Docker Compose configuration (`docker/docker-compose.yml`)
  - Docker ignore file (`.dockerignore`)
  
- **Setup Scripts**
  - Automated setup for Linux/Mac (`scripts/setup.sh`)
  - Automated setup for Windows (`scripts/setup.bat`)
  - Model download utility (`scripts/download_models.py`)
  
- **Configuration**
  - YAML configuration file (`config.yaml`)
  - Python dependencies (`requirements.txt`)
  - Git ignore file (`.gitignore`)

### Technical Details
- Python 3.10+ support
- Streamlit 1.30+ for web interface
- PyTorch 2.1+ for model inference
- HuggingFace Transformers integration
- Type hints throughout codebase
- Comprehensive error handling
- Modular architecture for extensibility

---

## Version History Summary

- **0.2.0** - Production improvements (logging, caching, validation, UI enhancements)
- **0.1.0** - Initial release (project foundation, model framework, documentation)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for information on how to contribute to this project.

## Links

- [GitHub Repository](https://github.com/dispersi0no/CHAT-VLM-LLM)
- [Documentation](https://github.com/dispersi0no/CHAT-VLM-LLM/tree/main/docs)
- [Issue Tracker](https://github.com/dispersi0no/CHAT-VLM-LLM/issues)