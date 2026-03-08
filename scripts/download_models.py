#!/usr/bin/env python3
"""Script to pre-download models from HuggingFace."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml

from models import ModelLoader


def download_model(model_key: str) -> bool:
    """
    Download a model from HuggingFace.

    Args:
        model_key: Model identifier from config

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"\n{'='*50}")
        print(f"Downloading: {model_key}")
        print(f"{'='*50}\n")

        model = ModelLoader.load_model(model_key)
        print(f"\n✅ {model_key} downloaded successfully")

        # Unload to free memory
        ModelLoader.unload_model(model_key)
        return True

    except Exception as e:
        print(f"\n❌ Error downloading {model_key}: {e}")
        return False


def main():
    """Main function."""
    print("\n" + "=" * 50)
    print("ChatVLMLLM Model Download Script")
    print("=" * 50)

    # Load config
    config_path = project_root / "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    available_models = list(config["models"].keys())

    print("\nAvailable models:")
    for i, model_key in enumerate(available_models, 1):
        model_config = config["models"][model_key]
        print(f"{i}. {model_key} - {model_config['name']}")

    print("\nOptions:")
    print("- Enter model number to download specific model")
    print("- Enter 'all' to download all models")
    print("- Enter 'q' to quit")

    choice = input("\nYour choice: ").strip().lower()

    if choice == "q":
        print("\nExiting...")
        return

    if choice == "all":
        print("\nDownloading all models...")
        results = {}
        for model_key in available_models:
            results[model_key] = download_model(model_key)

        print("\n" + "=" * 50)
        print("Download Summary")
        print("=" * 50)
        for model_key, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"{model_key}: {status}")

    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(available_models):
            model_key = available_models[idx]
            download_model(model_key)
        else:
            print("\n❌ Invalid model number")

    else:
        print("\n❌ Invalid choice")

    print("\nModels are cached in: ~/.cache/huggingface/")
    print("\nDone! 🎉\n")


if __name__ == "__main__":
    main()
