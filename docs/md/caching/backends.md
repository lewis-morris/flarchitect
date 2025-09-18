[← Back to Caching index](index.md)

# Backends
Set API_CACHE_TYPE <configuration.html#CACHE_TYPE> to a supported cache:
- With `flask-caching` installed: `RedisCache`, `SimpleCache`, etc.
- Without `flask-caching`: only `SimpleCache` (in‑memory per process).
Timeout is controlled by API_CACHE_TIMEOUT <configuration.html#CACHE_TIMEOUT>.

