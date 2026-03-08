#!/usr/bin/env python3
"""Check if the environment is properly set up."""

import importlib.util
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(
            f"❌ Python {version.major}.{version.minor}.{version.micro} (3.10+ required)"
        )
        return False


def check_package(package_name: str) -> bool:
    """Check if a package is installed."""
    spec = importlib.util.find_spec(package_name)
    if spec is not None:
        print(f"✅ {package_name}")
        return True
    else:
        print(f"❌ {package_name}")
        return False


def check_cuda():
    """Check CUDA availability."""
    try:
        import torch

        if torch.cuda.is_available():
            print(
                f"✅ CUDA {torch.version.cuda} (GPU: {torch.cuda.get_device_name(0)})"
            )
            return True
        else:
            print("⚠️  CUDA not available (CPU mode will be used)")
            return False
    except ImportError:
        print("❌ PyTorch not installed")
        return False


def check_directories():
    """Check if required directories exist."""
    required_dirs = ["models", "utils", "ui", "tests", "examples", "logs", "results"]

    all_exist = True
    for dir_name in required_dirs:
        path = Path(dir_name)
        if path.exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"⚠️  {dir_name}/ (creating...)")
            path.mkdir(exist_ok=True)
            all_exist = False

    return all_exist


def check_config_files():
    """Check if configuration files exist."""
    config_files = ["config.yaml", "requirements.txt", ".env.example"]

    all_exist = True
    for file_name in config_files:
        path = Path(file_name)
        if path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name}")
            all_exist = False

    return all_exist


def main():
    """Main check function."""
    print("\n" + "=" * 50)
    print("ChatVLMLLM Environment Check")
    print("=" * 50 + "\n")

    checks = []

    # Python version
    print("[1/5] Python Version")
    checks.append(check_python_version())
    print()

    # Required packages
    print("[2/5] Required Packages")
    required_packages = [
        "streamlit",
        "torch",
        "transformers",
        "pillow",
        "numpy",
        "yaml",
    ]
    package_checks = [check_package(pkg) for pkg in required_packages]
    checks.append(all(package_checks))
    print()

    # CUDA
    print("[3/5] CUDA Support")
    check_cuda()
    print()

    # Directories
    print("[4/5] Project Directories")
    checks.append(check_directories())
    print()

    # Config files
    print("[5/5] Configuration Files")
    checks.append(check_config_files())
    print()

    # Summary
    print("=" * 50)
    if all(checks):
        print("✅ Environment is ready!")
        print("\nRun: streamlit run app.py")
        return 0
    else:
        print("⚠️  Some checks failed")
        print("\nRun: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
