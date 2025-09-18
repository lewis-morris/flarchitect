[← Back to Advanced Configuration index](index.md)

# Caching backends
`flarchitect` can cache GET responses when API_CACHE_TYPE <configuration.html#CACHE_TYPE> is set. If
`flask-caching` is installed, any of its backends (such as Redis or
Memcached) may be used. When `flask-caching` is **not** available and
API_CACHE_TYPE <configuration.html#CACHE_TYPE> is `"SimpleCache"`, a bundled
`SimpleCache` provides an in-memory fallback. This lightweight cache is
cleared when the process restarts and stores data only for the current
worker, making it suitable for development or tests rather than
production.
Compared to `flask-caching` it lacks distributed backends, cache
invalidation features and the broader decorator API. For deployments with
multiple workers or where persistence matters, install `flask-caching`
and configure a production-ready backend instead.
The rate limiter also stores counters in a cache backend. When initialising,
`flarchitect` will automatically use a locally running Memcached,
Redis or MongoDB instance. To point to a specific backend, supply a storage
URI:
```
class Config:
    API_RATE_LIMIT_STORAGE_URI = "redis://redis.example.com:6379"
```
If no backend is available, the limiter falls back to in-memory storage
with rate-limit headers enabled by default. In production, you might point
to a shared Redis cluster so that multiple application servers enforce the
same limits.
You can also cache `GET` responses by choosing a backend with
API_CACHE_TYPE <configuration.html#CACHE_TYPE>. When flask-caching <[https://flask-caching.readthedocs.io/](https://flask-caching.readthedocs.io/)>
is installed, set API_CACHE_TYPE <configuration.html#CACHE_TYPE> to any supported backend such as
`RedisCache`. If the extension is missing, specifying `SimpleCache`
activates a small in-memory cache bundled with `flarchitect`; any other
value will raise a RuntimeError. Use API_CACHE_TIMEOUT <configuration.html#CACHE_TIMEOUT> to control
how long items remain cached.
Example `RedisCache` setup with a `SimpleCache` fallback and a cached
`GET` request:
```
from flask import Flask
from flarchitect import Architect
import time

app = Flask(__name__)
try:
    import flask_caching  # requires installing ``flask-caching``
    app.config["API_CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = "redis://localhost:6379/0"
except ModuleNotFoundError:
    app.config["API_CACHE_TYPE"] = "SimpleCache"

arch = Architect(app)

@app.get("/time")
def get_time():
    return {"now": time.time()}

with app.test_client() as client:
    client.get("/time")  # first call stored in cache
    client.get("/time")  # second call served from cache
```
For a runnable example demonstrating cached responses see the caching demo <[https://github.com/lewis-morris/flarchitect/tree/master/demo/caching](https://github.com/lewis-morris/flarchitect/tree/master/demo/caching)>.
After securing throughput, you can also shape what your clients see in each
payload.

