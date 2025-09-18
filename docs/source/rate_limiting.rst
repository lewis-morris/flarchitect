Rate Limiting
=============

Protect your API from abuse and manage throughput with flexible rate limits.
You can set global limits, per‑model limits, and choose a storage backend for
counters.

Configuration
-------------

Global limit::

    class Config:
        API_RATE_LIMIT = "200 per day"

Per‑model limit::

    class Book(db.Model):
        class Meta:
            rate_limit = "5 per minute"  # API_RATE_LIMIT


Storage backends
----------------

The limiter stores counters in a cache backend. Provide a storage URI:

.. code:: python

    class Config:
        API_RATE_LIMIT_STORAGE_URI = "redis://redis.example.com:6379"

If none is provided, an in‑memory fallback is used (suitable for development
only). For production, use Redis, Memcached, or MongoDB via a shared backend.

