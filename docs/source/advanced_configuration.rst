Advanced Configuration
======================

Beyond the basics, **flarchitect** offers several advanced options for fine-tuning
API behaviour. This guide covers rate limiting and cache configuration.

Rate limiting
-------------

Rate limits can be applied globally, per HTTP method or per model.

**Global limit**

.. code:: python

    class Config:
        API_RATE_LIMIT = "200 per day"

**Method specific**

.. code:: python

    class Config:
        API_GET_RATE_LIMIT = "100 per minute"
        API_POST_RATE_LIMIT = "10 per minute"

**Model specific**

.. code:: python

    class Book(db.Model):
        __tablename__ = "book"

        class Meta:
            rate_limit = "5 per minute"      # becomes API_RATE_LIMIT
            get_rate_limit = "10 per minute"  # becomes API_GET_RATE_LIMIT

Caching backends
----------------

The rate limiter stores counters in a cache backend. When initialising,
``flarchitect`` will automatically use a locally running Memcached,
Redis or MongoDB instance. To point to a specific backend, supply a
storage URI:

.. code:: python

    class Config:
        API_RATE_LIMIT_STORAGE_URI = "redis://redis.example.com:6379"

If no backend is available, the limiter falls back to in-memory storage
with rate-limit headers enabled by default.

CORS
----

To enable `Cross-Origin Resource Sharing (CORS) <https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS>`_
for your API, set :data:`API_ENABLE_CORS` to ``True`` in the application
configuration. When active, CORS headers are applied to matching routes
defined in :data:`CORS_RESOURCES`.

``CORS_RESOURCES`` accepts a mapping of URL patterns to their respective
options, mirroring the format used by `Flask-CORS <https://flask-cors.readthedocs.io/>`_.

.. code:: python

    class Config:
        API_ENABLE_CORS = True
        CORS_RESOURCES = {
            r"/api/*": {"origins": "*"}
        }

See the :doc:`configuration <configuration>` page for the full list of
available CORS settings.

