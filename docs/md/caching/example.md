[← Back to Caching index](index.md)

# Example
```
try:
    import flask_caching
    app.config["API_CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = "redis://localhost:6379/0"
except ModuleNotFoundError:
    app.config["API_CACHE_TYPE"] = "SimpleCache"
```

