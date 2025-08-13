"""Demo application demonstrating response caching."""

from __future__ import annotations

from demo.model_extension.model import create_app

# Configure a simple in-memory cache with a short timeout.
app = create_app({"API_CACHE_TYPE": "SimpleCache", "API_CACHE_TIMEOUT": 1})
