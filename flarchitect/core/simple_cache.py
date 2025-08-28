"""Simple in-memory cache backend for environments without :mod:`flask_caching`.

This fallback cache implements a very small subset of the ``flask_caching``
interface required by the tests.  It provides an in-memory key/value store with
per-item timeouts and a ``cached`` decorator used by :class:`~flarchitect.core.routes.RouteCreator`.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import request


class SimpleCache:
    """In-memory cache with an API similar to ``flask_caching``'s ``Cache``.

    Args:
        default_timeout: Default cache timeout in seconds.

    Methods:
        clear: Remove all entries from the cache.
    """

    def __init__(self, default_timeout: int = 300) -> None:
        self.default_timeout = default_timeout
        self._cache: dict[str, tuple[float, Any]] = {}

    def clear(self) -> None:
        """Clear all data from the cache."""

        self._cache.clear()

    def init_app(self, app) -> None:  # type: ignore[no-untyped-def]
        """Initialise the cache for a Flask application.

        This implementation stores data in process memory, so no explicit
        initialisation work is required.  The method is provided to mirror the
        ``flask_caching`` API.
        """

    def _expires(self, timeout: int | None) -> float:
        """Return an absolute expiry timestamp.

        Args:
            timeout: Timeout in seconds. ``None`` uses ``self.default_timeout``.

        Returns:
            The epoch time when the cache entry should expire.
        """

        return time.time() + (timeout if timeout is not None else self.default_timeout)

    def _purge(self) -> None:
        """Remove expired entries from the cache."""

        now = time.time()
        expired = [key for key, (expires, _value) in self._cache.items() if expires < now]
        for key in expired:
            self._cache.pop(key, None)

    def get(self, key: str) -> Any | None:
        """Retrieve a cached value if present and not expired.

        Args:
            key: Cache key to retrieve.

        Returns:
            The cached value if found and valid; otherwise ``None``.
        """

        self._purge()
        record = self._cache.get(key)
        if record is None:
            return None
        _expires, value = record
        return value

    def set(self, key: str, value: Any, timeout: int | None = None) -> None:
        """Store ``value`` in the cache with the given ``timeout``."""

        self._cache[key] = (self._expires(timeout), value)

    def cached(self, timeout: int | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to cache view function responses.

        Args:
            timeout: Time in seconds before the cache entry expires.

        Returns:
            A decorator that caches the wrapped function's response keyed by the
            request's full path.
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                key = request.full_path  # type: ignore[union-attr]
                cached = self.get(key)
                if cached is not None:
                    return cached
                value = func(*args, **kwargs)
                self.set(key, value, timeout)
                return value

            return wrapper

        return decorator
