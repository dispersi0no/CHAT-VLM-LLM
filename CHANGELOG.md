# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Fine-tuning support
- Cloud deployment guide
- Performance benchmarks
- Security hardening (env validation, input sanitization)

## [0.4.0] - 2026-03-09

### Added
- **CI/CD Pipeline**: Full GitHub Actions workflow — black, isort, mypy, pytest with coverage, 15% coverage gate (#76)
- **Test Suite**: 162+ new tests across 7 PRs:
  - Unit tests for utilities and constants (#80)
  - Mock-based inference pipeline tests (#85)
  - FastAPI endpoint tests with TestClient (#87)
  - Docker container manager tests — 42 cases (#89)
  - vLLM adapter tests — 48 cases (#90)
  - UI utility tests (bbox, components, message_renderer) — 52 cases (#91)
- **Strict Typing**: `py.typed` marker (PEP 561), `strict = true` mypy config, type annotations across 9 core modules (#92)
- **Structured Logging**: Centralized `utils/logging_config.py` with `setup_logging()`, `logger.exception()` in all except blocks alongside `st.error()` (#93)
- **Pre-commit Hooks**: Enhanced with `debug-statements`, `detect-private-key`, `check-ast`, `check-merge-conflict`, `check-json`, `check-toml`, mypy mirror (#94)
- **Project Config**: `pyproject.toml` with black, isort, pytest, mypy sections (#86)

### Changed
- **Code Style**: Full black + isort formatting pass across entire codebase (#77)
- **Refactoring**:
  - Renamed `dots_ocr_final` → `dots_ocr` — removed legacy suffix (#78)
  - Consolidated duplicated `unload()` methods into single base implementation (#81)
  - Cleaned `__init__` + tokenizer patterns across model wrappers (#83)
  - Split `ui/sidebar.py` (17KB) into 8 focused helper functions (#88)
- **Logging**: `start_system.py` / `stop_system.py` — `print()` → `logger.info/error`, bare `except:` → specific exception types (#93)
- **Pre-commit**: Bumped versions — pre-commit-hooks v5.0.0, black 24.10.0, flake8 7.1.1 (#94)

### Fixed
- **Bug**: Missing `unload()` method in Qwen3VL model wrapper — caused memory leak on model switch (#82)

### Removed
- Dead code cleanup — unused imports, unreachable branches, stale comments (#79)

### Documentation
- README rewrite — updated architecture, models, GPU requirements (#84)
- Pre-commit hooks section added to README_DEV.md (#94)

## [0.3.1] - 2026-03-08

### Fixed
- **Security**: Replaced pickle cache with JSON serialization (RCE vulnerability) (#71)
- **Security**: Removed logger side-effect on import — `setup_logger()` now explicit (#71)
- **CI/CD**: Fixed dependency installation order in GitHub Actions (#72)
- **CI/CD**: Pinned `qwen-vl-utils==0.0.10` to prevent breakage (#72)

### Added
- **Tests**: 45 new tests — API endpoints, RateLimiter, file validation, JSON cache (#74)
- **Tests**: `tests/conftest.py` with shared fixtures and sys.path setup (#74)
- **Docs**: Updated architecture, models, GPU requirements for current state (#73)

### Changed
- `utils/cache.py` stores `.json` files instead of `.pkl` with `default=str` fallback (#71)
- `utils/logger.py` no longer auto-configures logging on import (#71)
- `requirements.txt` CI extras: `httpx`, `qwen-vl-utils==0.0.10` (#72)

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
  - Rate limiting per IP
  - File validation (size, extension, PIL verify)

- **New Models**
  - dots.ocr integration (SOTA document parser, 100+ languages)
  - Qwen3-VL 2B with 32-language OCR, 256K context
  - Phi-3.5 Vision (vLLM-only)

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

- **0.4.0** - Code quality engineering: CI/CD, 162+ tests, strict typing, structured logging, pre-commit hooks
- **0.3.1** - Security fixes, CI/CD fixes, test coverage expansion
- **0.3.0** - vLLM support, FastAPI API, project audit & cleanup
- **0.2.0** - Production improvements (logging, caching, validation, UI enhancements)
- **0.1.0** - Initial release (project foundation, model framework, documentation)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for information on how to contribute to this project.

## Links

- [GitHub Repository](https://github.com/dispersi0no/CHAT-VLM-LLM)
- [Documentation](https://github.com/dispersi0no/CHAT-VLM-LLM/tree/main/docs)
- [Issue Tracker](https://github.com/dispersi0no/CHAT-VLM-LLM/issues)
