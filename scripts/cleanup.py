#!/usr/bin/env python3
"""Clean up temporary files and caches."""

import shutil
import sys
from pathlib import Path


def get_directory_size(path: Path) -> int:
    """Calculate total size of directory."""
    total = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
    except Exception:
        pass
    return total


def format_size(size: int) -> str:
    """Format size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def clean_cache():
    """Clean application cache."""
    cache_dirs = [Path(".cache"), Path("__pycache__"), Path(".pytest_cache")]

    total_freed = 0

    for cache_dir in cache_dirs:
        if cache_dir.exists():
            size = get_directory_size(cache_dir)
            try:
                if cache_dir.name == "__pycache__":
                    # Find all __pycache__ directories
                    for pycache in Path(".").rglob("__pycache__"):
                        shutil.rmtree(pycache, ignore_errors=True)
                else:
                    shutil.rmtree(cache_dir)
                print(f"✅ Removed {cache_dir} ({format_size(size)})")
                total_freed += size
            except Exception as e:
                print(f"❌ Failed to remove {cache_dir}: {e}")
        else:
            print(f"⏭️  {cache_dir} (doesn't exist)")

    return total_freed


def clean_logs():
    """Clean old log files."""
    logs_dir = Path("logs")

    if not logs_dir.exists():
        print("⏭️  logs/ (doesn't exist)")
        return 0

    total_freed = 0
    log_files = list(logs_dir.glob("*.log"))

    if not log_files:
        print("⏭️  No log files found")
        return 0

    for log_file in log_files:
        size = log_file.stat().st_size
        try:
            log_file.unlink()
            print(f"✅ Removed {log_file.name} ({format_size(size)})")
            total_freed += size
        except Exception as e:
            print(f"❌ Failed to remove {log_file.name}: {e}")

    return total_freed


def clean_temp_files():
    """Clean temporary files."""
    patterns = ["*.pyc", "*.pyo", "*.tmp", ".DS_Store", "Thumbs.db"]

    total_freed = 0

    for pattern in patterns:
        for temp_file in Path(".").rglob(pattern):
            size = temp_file.stat().st_size
            try:
                temp_file.unlink()
                print(f"✅ Removed {temp_file} ({format_size(size)})")
                total_freed += size
            except Exception as e:
                print(f"❌ Failed to remove {temp_file}: {e}")

    return total_freed


def main():
    """Main cleanup function."""
    print("\n" + "=" * 50)
    print("ChatVLMLLM Cleanup")
    print("=" * 50 + "\n")

    print("[1/3] Cleaning cache...")
    cache_freed = clean_cache()
    print()

    print("[2/3] Cleaning logs...")
    logs_freed = clean_logs()
    print()

    print("[3/3] Cleaning temporary files...")
    temp_freed = clean_temp_files()
    print()

    total = cache_freed + logs_freed + temp_freed

    print("=" * 50)
    print(f"✅ Cleanup complete! Freed {format_size(total)}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup interrupted by user")
        sys.exit(1)
