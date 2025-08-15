"""Tests for the :class:`SimpleCache` fallback cache implementation."""

import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

# Load ``SimpleCache`` directly from the source file so the tests work
# regardless of the working directory.
module_path = Path(__file__).resolve().parents[2] / "flarchitect" / "core" / "simple_cache.py"
SimpleCache = SourceFileLoader("simple_cache", str(module_path)).load_module().SimpleCache


def test_clear_removes_entries():
    cache = SimpleCache()
    cache.set("a", 1)
    assert cache.get("a") == 1
    cache.clear()
    assert cache.get("a") is None
    assert cache._cache == {}


def test_get_purges_expired_entries():
    cache = SimpleCache()
    cache.set("a", 1, timeout=1)
    cache.set("b", 2, timeout=5)
    time.sleep(1.1)
    assert cache.get("b") == 2
    assert "a" not in cache._cache


def test_cached_decorator_uses_cache():
    cache = SimpleCache()

    from flask import Flask

    app = Flask(__name__)
    calls = {"count": 0}

    @cache.cached(timeout=60)
    def view() -> str:
        calls["count"] += 1
        return "ok"

    with app.test_request_context("/cache-me"):
        assert view() == "ok"
        # Second call should hit the cache rather than invoking ``view`` again.
        assert view() == "ok"
    assert calls["count"] == 1
