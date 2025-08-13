# Caching Demo

This example shows how **flarchitect** caches GET responses. The cache backend is selected with `API_CACHE_TYPE` and entries expire after `API_CACHE_TIMEOUT` seconds.

If `flask_caching` is installed, its `Cache` class backs the demo. Otherwise it falls back to the lightweight `SimpleCache` implementation bundled with flarchitect.

## Run

```bash
pip install 'flarchitect[cache]'  # enables flask-caching
python demo/caching/app.py
```

Requests to `/api/authors/1` will return cached data until the timeout expires. The `/time` route demonstrates caching on a custom endpoint.
