"""Tests for utils/cache.py — JSON cache, expiration, decorator."""

import shutil
import tempfile
import time
from pathlib import Path

import pytest

from utils.cache import SimpleCache, cached


@pytest.fixture
def tmp_cache(tmp_path):
    """Create a SimpleCache in a temp directory."""
    return SimpleCache(str(tmp_path / "test_cache"))


class TestSimpleCache:
    """Tests for SimpleCache class."""

    def test_set_and_get(self, tmp_cache):
        tmp_cache.set("key1", {"text": "hello", "score": 0.95})
        result = tmp_cache.get("key1")
        assert result == {"text": "hello", "score": 0.95}

    def test_get_missing_returns_default(self, tmp_cache):
        assert tmp_cache.get("nonexistent") is None
        assert tmp_cache.get("nonexistent", default="fallback") == "fallback"

    def test_stores_as_json_files(self, tmp_cache):
        tmp_cache.set("key1", "value")
        files = list(Path(tmp_cache.cache_dir).glob("*.json"))
        assert len(files) == 1

    def test_no_pickle_files(self, tmp_cache):
        tmp_cache.set("key1", "value")
        pkl_files = list(Path(tmp_cache.cache_dir).glob("*.pkl"))
        assert len(pkl_files) == 0

    def test_size(self, tmp_cache):
        assert tmp_cache.size() == 0
        tmp_cache.set("a", 1)
        tmp_cache.set("b", 2)
        assert tmp_cache.size() == 2

    def test_clear(self, tmp_cache):
        tmp_cache.set("a", 1)
        tmp_cache.set("b", 2)
        tmp_cache.clear()
        assert tmp_cache.size() == 0

    def test_clear_removes_legacy_pkl(self, tmp_cache):
        legacy = Path(tmp_cache.cache_dir) / "legacy.pkl"
        legacy.write_text("fake")
        tmp_cache.clear()
        assert not legacy.exists()

    def test_expiration(self, tmp_cache):
        tmp_cache.set("key", "value")
        assert tmp_cache.get("key", max_age=10) == "value"
        assert tmp_cache.get("key", max_age=0) is None

    def test_overwrite(self, tmp_cache):
        tmp_cache.set("key", "old")
        tmp_cache.set("key", "new")
        assert tmp_cache.get("key") == "new"

    def test_stores_lists(self, tmp_cache):
        tmp_cache.set("list", [1, 2, 3])
        assert tmp_cache.get("list") == [1, 2, 3]

    def test_stores_nested_dicts(self, tmp_cache):
        data = {"a": {"b": {"c": 42}}}
        tmp_cache.set("nested", data)
        assert tmp_cache.get("nested") == data

    def test_handles_non_serializable_with_default_str(self, tmp_cache):
        from datetime import datetime

        now = datetime.now()
        tmp_cache.set("dt", {"timestamp": now})
        result = tmp_cache.get("dt")
        assert isinstance(result["timestamp"], str)


class TestCachedDecorator:
    """Tests for @cached decorator."""

    def test_caches_result(self, tmp_cache):
        call_count = 0

        @cached(tmp_cache)
        def expensive(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        assert expensive(5) == 10
        assert expensive(5) == 10
        assert call_count == 1

    def test_different_args_different_cache(self, tmp_cache):
        call_count = 0

        @cached(tmp_cache)
        def add(a, b):
            nonlocal call_count
            call_count += 1
            return a + b

        assert add(1, 2) == 3
        assert add(3, 4) == 7
        assert call_count == 2

    def test_respects_max_age(self, tmp_cache):
        call_count = 0

        @cached(tmp_cache, max_age=0)
        def compute():
            nonlocal call_count
            call_count += 1
            return 42

        compute()
        compute()
        assert call_count == 2
