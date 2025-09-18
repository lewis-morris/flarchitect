Caching
=======

Speed up repeated requests by caching GET responses. Use ``flask-caching`` for
production backends or a bundled simple cache for development.

Backends
--------

Set `API_CACHE_TYPE <configuration.html#CACHE_TYPE>`_ to a supported cache:

- With ``flask-caching`` installed: ``RedisCache``, ``SimpleCache``, etc.
- Without ``flask-caching``: only ``SimpleCache`` (in‑memory per process).

Timeout is controlled by `API_CACHE_TIMEOUT <configuration.html#CACHE_TIMEOUT>`_.

Example
-------

.. code:: python

    try:
        import flask_caching
        app.config["API_CACHE_TYPE"] = "RedisCache"
        app.config["CACHE_REDIS_URL"] = "redis://localhost:6379/0"
    except ModuleNotFoundError:
        app.config["API_CACHE_TYPE"] = "SimpleCache"

