"""Run with PYTHONPATH=. in the project environment."""

import hashlib
import json
import random
import statistics
import timeit
from unittest.mock import patch

from flarchitect.core import simple_cache


class CountingDict(dict):
    scans = 0

    def items(self):
        self.scans += 1
        return super().items()


clock = [100.0]
results = {}
with patch.object(simple_cache.time, "time", new=lambda: clock[0]):
    for size in (10, 1000, 10000):
        cache = simple_cache.SimpleCache(default_timeout=300)
        cache._cache = CountingDict()
        for i in range(size):
            cache.set(str(i), i)
        for _ in range(100):
            assert cache.get("0") == 0
        scans = cache._cache.scans
        results[str(size)] = {
            "scans_per_100_reads": scans,
            "hit_us": statistics.median(timeit.repeat(lambda cache=cache: cache.get("0"), repeat=5, number=1000)) / 1000 * 1e6,
        }
    rng = random.Random(42)
    cache = simple_cache.SimpleCache(default_timeout=5)
    trace = []
    for step in range(1000):
        operation = rng.choice(("set", "get", "get", "advance", "rollback", "clear"))
        key = str(rng.randrange(10))
        value = None
        if operation == "set":
            cache.set(key, step, timeout=rng.choice((None, -1, 0, 1, 5, 10)))
        elif operation == "get":
            value = cache.get(key)
        elif operation == "advance":
            clock[0] += rng.randrange(5)
        elif operation == "rollback":
            clock[0] -= rng.randrange(3)
        else:
            cache.clear()
        trace.append([operation, key, value, clock[0], sorted(cache._cache.items())])
results["trace_sha256"] = hashlib.sha256(json.dumps(trace).encode()).hexdigest()
print(json.dumps(results, indent=2))
