import time
from importlib.machinery import SourceFileLoader

SimpleCache = (
    SourceFileLoader("simple_cache", "flarchitect/core/simple_cache.py")
    .load_module()
    .SimpleCache
)


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
