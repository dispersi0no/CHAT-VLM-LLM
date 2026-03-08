"""Utilities for managing HuggingFace model cache."""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ModelCacheManager:
    """Manager for HuggingFace model cache."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize cache manager.

        Args:
            cache_dir: Custom cache directory (None for default HF cache)
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Default HuggingFace cache location
            self.cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def find_model_in_cache(self, model_id: str) -> Optional[Path]:
        """
        Find model in HuggingFace cache.

        Args:
            model_id: Model identifier (e.g., 'stepfun-ai/GOT-OCR2_0')

        Returns:
            Path to cached model or None if not found
        """
        # HuggingFace cache uses format: models--org--model-name
        cache_model_name = model_id.replace("/", "--")
        model_path = self.cache_dir / f"models--{cache_model_name}"

        if model_path.exists():
            # Check if it has snapshots (downloaded model)
            snapshots_dir = model_path / "snapshots"
            if snapshots_dir.exists() and list(snapshots_dir.iterdir()):
                return model_path

        return None

    def is_model_cached(self, model_id: str) -> bool:
        """
        Check if model is in cache.

        Args:
            model_id: Model identifier

        Returns:
            True if model is cached
        """
        return self.find_model_in_cache(model_id) is not None

    def get_cached_snapshot_path(self, model_id: str) -> Optional[Path]:
        """
        Get path to latest cached snapshot.

        Args:
            model_id: Model identifier

        Returns:
            Path to snapshot directory or None
        """
        model_path = self.find_model_in_cache(model_id)
        if not model_path:
            return None

        snapshots_dir = model_path / "snapshots"
        if not snapshots_dir.exists():
            return None

        # Get latest snapshot
        snapshots = sorted(snapshots_dir.iterdir(), key=lambda x: x.stat().st_mtime)
        if snapshots:
            return snapshots[-1]

        return None

    def get_model_size(self, model_id: str) -> Optional[int]:
        """
        Get size of cached model in bytes.

        Args:
            model_id: Model identifier

        Returns:
            Size in bytes or None if not cached
        """
        model_path = self.find_model_in_cache(model_id)
        if not model_path:
            return None

        total_size = 0
        for item in model_path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size

        return total_size

    def list_cached_models(self) -> List[Dict[str, any]]:
        """
        List all cached models.

        Returns:
            List of model information dictionaries
        """
        cached_models = []

        if not self.cache_dir.exists():
            return cached_models

        for model_dir in self.cache_dir.glob("models--*"):
            # Parse model ID from directory name
            model_name = model_dir.name.replace("models--", "").replace("--", "/")

            # Get size
            size = 0
            for item in model_dir.rglob("*"):
                if item.is_file():
                    size += item.stat().st_size

            # Check if has snapshots
            snapshots_dir = model_dir / "snapshots"
            has_snapshots = snapshots_dir.exists() and list(snapshots_dir.iterdir())

            if has_snapshots:
                cached_models.append(
                    {
                        "model_id": model_name,
                        "path": model_dir,
                        "size_bytes": size,
                        "size_mb": round(size / (1024 * 1024), 2),
                        "size_gb": round(size / (1024 * 1024 * 1024), 2),
                    }
                )

        return sorted(cached_models, key=lambda x: x["size_bytes"], reverse=True)

    def delete_model_cache(self, model_id: str) -> bool:
        """
        Delete model from cache.

        Args:
            model_id: Model identifier

        Returns:
            True if deleted successfully
        """
        model_path = self.find_model_in_cache(model_id)
        if not model_path:
            return False

        try:
            shutil.rmtree(model_path)
            return True
        except Exception:
            return False

    def get_cache_info(self) -> Dict[str, any]:
        """
        Get cache information.

        Returns:
            Dictionary with cache statistics
        """
        cached_models = self.list_cached_models()
        total_size = sum(m["size_bytes"] for m in cached_models)

        return {
            "cache_dir": str(self.cache_dir),
            "model_count": len(cached_models),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
            "models": cached_models,
        }


def check_model_availability(model_id: str) -> Tuple[bool, Optional[str]]:
    """
    Check if model is available (cached or can be downloaded).

    Args:
        model_id: Model identifier

    Returns:
        Tuple of (is_available, status_message)
    """
    cache_manager = ModelCacheManager()

    # Check cache first
    if cache_manager.is_model_cached(model_id):
        snapshot_path = cache_manager.get_cached_snapshot_path(model_id)
        size = cache_manager.get_model_size(model_id)
        size_gb = round(size / (1024 * 1024 * 1024), 2) if size else 0

        return True, f"Found in cache ({size_gb} GB): {snapshot_path}"

    # Not in cache - can be downloaded
    return False, "Not in cache - will download on first use"


def format_size(size_bytes: int) -> str:
    """
    Format size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
