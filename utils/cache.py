"""Caching utilities for model results and processed images."""

import hashlib
import pickle
from pathlib import Path
from typing import Any, Optional, Callable
from functools import wraps
import time

_CACHE_MISS = object()


class SimpleCache:
    """Simple file-based cache for storing results."""
    
    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        # Create hash of key for filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.pkl"
    
    def get(self, key: str, max_age: Optional[int] = None, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            max_age: Maximum age in seconds (None for no expiration)
            default: Value to return on cache miss (default: None)
            
        Returns:
            Cached value or default if not found/expired
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return default
        
        # Check age if specified
        if max_age is not None:
            file_age = time.time() - cache_path.stat().st_mtime
            if file_age > max_age:
                cache_path.unlink()  # Remove expired cache
                return default
        
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            print(f"Failed to cache value: {e}")
    
    def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
    
    def size(self) -> int:
        """Get number of cached items."""
        return len(list(self.cache_dir.glob("*.pkl")))


def cached(cache: SimpleCache, max_age: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        cache: Cache instance
        max_age: Maximum cache age in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = "|".join(key_parts)
            
            # Try to get from cache
            result = cache.get(cache_key, max_age, default=_CACHE_MISS)
            if result is not _CACHE_MISS:
                return result
            
            # Compute result and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator


# Global cache instance
app_cache = SimpleCache(".cache/app")