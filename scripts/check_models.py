#!/usr/bin/env python3
"""Check status of models in HuggingFace cache."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml

from models.model_loader import ModelLoader
from utils.model_cache import ModelCacheManager, format_size


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}\n")


def check_configured_models():
    """Check models defined in config.yaml."""
    print_section("Configured Models")

    config_path = project_root / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    for model_key, model_config in config["models"].items():
        print(f"\n🤖 {model_config['name']}")
        print(f"   Key: {model_key}")
        print(f"   Path: {model_config.get('model_path', 'N/A')}")

        # Check cache status
        is_cached, msg = ModelLoader.check_model_cache(model_key)

        if is_cached:
            print(f"   Status: ✅ Cached")
            print(f"   Info: {msg}")
        else:
            print(f"   Status: ⚠️  Not cached")
            print(f"   Info: {msg}")


def check_cache_status():
    """Check HuggingFace cache status."""
    print_section("Cache Status")

    cache_info = ModelLoader.get_cache_info()

    print(f"Cache Directory: {cache_info['cache_dir']}")
    print(f"Total Models: {cache_info['model_count']}")
    print(f"Total Size: {cache_info['total_size_gb']:.2f} GB")

    if cache_info["model_count"] > 0:
        print("\nCached Models:")
        for model in cache_info["models"]:
            print(f"\n  ✅ {model['model_id']}")
            print(f"     Size: {model['size_gb']:.2f} GB")
            print(f"     Path: {model['path']}")
    else:
        print("\n⚠️  No models in cache")


def check_loaded_models():
    """Check currently loaded models in memory."""
    print_section("Loaded Models (in memory)")

    loaded = ModelLoader.get_loaded_models()

    if loaded:
        print("Currently loaded:")
        for model_key in loaded:
            print(f"  ✅ {model_key}")
    else:
        print("⚠️  No models loaded in memory")


def provide_recommendations():
    """Provide recommendations based on cache status."""
    print_section("Recommendations")

    cache_info = ModelLoader.get_cache_info()
    config_path = project_root / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Check which models need downloading
    models_to_download = []
    for model_key in config["models"].keys():
        is_cached, _ = ModelLoader.check_model_cache(model_key)
        if not is_cached:
            models_to_download.append(model_key)

    if models_to_download:
        print("📥 Models need to be downloaded:")
        for model_key in models_to_download:
            model_config = config["models"][model_key]
            print(f"  - {model_key} ({model_config['name']})")

        print("\n🚀 To download models, run:")
        print("   python scripts/download_models.py")
        print(
            "\n   Or start the app - models will download automatically on first use:"
        )
        print("   streamlit run app.py")
    else:
        print("✅ All configured models are cached and ready!")
        print("\n🚀 You can start the application:")
        print("   streamlit run app.py")

    if cache_info["total_size_gb"] > 20:
        print(f"\n⚠️  Cache size is large ({cache_info['total_size_gb']:.1f} GB)")
        print("   You can clean unused models with:")
        print("   python scripts/cleanup.py")


def main():
    """Main function."""
    print("\n" + "=" * 60)
    print("ChatVLMLLM Model Status Checker")
    print("=" * 60)

    try:
        check_configured_models()
        check_cache_status()
        check_loaded_models()
        provide_recommendations()

        print("\n" + "=" * 60)
        print("✅ Check complete!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
