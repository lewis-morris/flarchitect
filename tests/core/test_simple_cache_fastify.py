"""Behavior and scan-cost regression checks for the fallback cache."""

import importlib.util
from pathlib import Path
from threading import Event, Thread, current_thread

import pytest

module_path = Path(__file__).resolve().parents[2] / "flarchitect" / "core" / "simple_cache.py"
spec = importlib.util.spec_from_file_location("simple_cache_fastify", module_path)
assert spec and spec.loader
simple_cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simple_cache)


@pytest.fixture
def clock(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(simple_cache.time, "time", lambda: now[0])
    return now


@pytest.mark.parametrize("timeout,expires", [(None, 105), (0, 100), (-1, 99), (20, 120)])
def test_expiry_boundary_and_timeout_semantics(clock, timeout, expires):
    cache = simple_cache.SimpleCache(default_timeout=5)
    cache.set("key", "value", timeout=timeout)
    assert cache._cache["key"][0] == expires
    clock[0] = expires
    assert cache.get("key") == "value"
    clock[0] += 0.001
    assert cache.get("key") is None


def test_overwrites_and_successive_global_expiration(clock):
    cache = simple_cache.SimpleCache()
    cache.set("later", "old", timeout=1)
    cache.set("later", "new", timeout=20)
    cache.set("earlier", "old", timeout=30)
    cache.set("earlier", "new", timeout=5)
    clock[0] = 102
    assert cache.get("later") == "new"
    clock[0] = 106
    assert cache.get("missing") is None
    assert cache._cache == {"later": (120, "new")}
    clock[0] = 121
    assert cache.get("missing") is None
    assert cache._cache == {}


def test_clock_rollback_and_clear_reuse(clock):
    cache = simple_cache.SimpleCache()
    cache.set("first", 1, timeout=10)
    clock[0] = 90
    cache.set("second", 2, timeout=5)
    assert cache.get("first") == 1
    clock[0] = 96
    assert cache.get("second") is None
    assert cache.get("first") == 1
    cache.clear()
    cache.set("third", 3, timeout=0)
    assert cache.get("third") == 3
    clock[0] = 97
    assert cache.get("third") is None
    assert cache._cache == {}


def test_cache_hits_skip_scans_until_expiration(clock):
    class CountingDict(dict):
        scans = 0

        def items(self):
            self.scans += 1
            return super().items()

    cache = simple_cache.SimpleCache()
    cache._cache = CountingDict()
    for index in range(1000):
        cache.set(str(index), index, timeout=10)
    for index in range(100):
        assert cache.get(str(index)) == index
    clock[0] = 110
    assert cache.get("0") == 0
    assert cache._cache.scans == 0
    clock[0] = 111
    assert cache.get("missing") is None
    assert cache._cache.scans == 1
    assert cache._cache == {}
    assert cache.get("missing") is None
    assert cache._cache.scans == 1


def test_concurrent_set_cannot_lose_earlier_expiry_during_purge(clock):
    cache = simple_cache.SimpleCache()
    cache.set("expired", "old", timeout=1)
    cache.set("survivor", "keep", timeout=100)
    clock[0] = 102
    scanning = Event()
    setter_attempted = Event()
    setter_finished = Event()
    failures = []
    real_lock = cache._lock

    class ObservedLock:
        def __enter__(self):
            if current_thread().name == "cache-setter":
                setter_attempted.set()
            return real_lock.__enter__()

        def __exit__(self, *args):
            return real_lock.__exit__(*args)

    class PausedDict(dict):
        def items(self):
            scanning.set()
            assert setter_attempted.wait(5), "setter never attempted its write"
            assert not setter_finished.is_set(), "set ran during the purge scan"
            return super().items()

    cache._lock = ObservedLock()
    cache._cache = PausedDict(cache._cache)

    def write_during_purge():
        try:
            assert scanning.wait(5), "purge never started"
            cache.set("new", "short lived", timeout=-1)
            setter_finished.set()
        except BaseException as exc:
            failures.append(exc)

    setter = Thread(target=write_during_purge, name="cache-setter", daemon=True)
    setter.start()
    try:
        assert cache.get("survivor") == "keep"
    finally:
        setter.join(timeout=5)
    assert not setter.is_alive()
    assert not failures
    assert setter_finished.is_set()
    cache._cache = dict(cache._cache)
    assert cache.get("new") is None
    assert cache._cache == {"survivor": (200, "keep")}


def test_expired_value_finalizer_preserves_new_earlier_expiry(clock):
    cache = simple_cache.SimpleCache()

    class InsertOnDeletion:
        def __del__(self):
            cache.set("from-finalizer", "expired", timeout=-1)

    cache.set("expired", InsertOnDeletion(), timeout=1)
    # Keep the loop's last value alive independently of the expired object.
    cache.set("survivor", "keep", timeout=100)
    clock[0] = 102
    assert cache.get("survivor") == "keep"
    assert "from-finalizer" in cache._cache
    assert cache.get("from-finalizer") is None
    assert cache._cache == {"survivor": (200, "keep")}


@pytest.mark.parametrize("value", [0, False, ""])
def test_decorator_caches_falsy_values(clock, value):
    from flask import Flask

    cache = simple_cache.SimpleCache()
    calls = []

    @cache.cached()
    def view():
        calls.append(True)
        return value

    with Flask(__name__).test_request_context("/cached"):
        assert view() == value
        assert view() == value
    assert len(calls) == 1


def test_decorated_view_runs_outside_cache_lock(clock):
    from flask import Flask

    cache = simple_cache.SimpleCache()
    written = Event()
    threads = []

    @cache.cached()
    def view():
        def write():
            cache.set("other", "available")
            written.set()

        worker = Thread(target=write, daemon=True)
        threads.append(worker)
        worker.start()
        assert written.wait(5), "view retained the cache lock"
        return "response"

    try:
        with Flask(__name__).test_request_context("/cached"):
            assert view() == "response"
    finally:
        for worker in threads:
            worker.join(timeout=5)
    assert all(not worker.is_alive() for worker in threads)
    assert cache.get("other") == "available"


def test_clear_preserves_expiry_of_finalizer_insertions(clock):
    cache = simple_cache.SimpleCache()

    class InsertOnDeletion:
        def __del__(self):
            cache.set("from-finalizer", "expired", timeout=-1)

    cache.set("original", InsertOnDeletion())
    cache.clear()
    assert "from-finalizer" in cache._cache
    assert cache.get("from-finalizer") is None
    assert cache._cache == {}
