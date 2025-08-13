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

Soft deletes
------------

Rather than removing records from the database, models can be "soft"
deleted by toggling an attribute value.

.. code:: python

    class Config:
        API_SOFT_DELETE = True
        API_SOFT_DELETE_ATTRIBUTE = "deleted"
        API_SOFT_DELETE_VALUES = (False, True)

    class Book(db.Model):
        __tablename__ = "book"
        deleted = db.Column(db.Boolean, default=False)

.. tip::

    The ``API_SOFT_DELETE_VALUES`` tuple should hold the active and deleted
    states respectively.

Callbacks
---------

Custom callbacks let you hook into the request lifecycle to run your own
logic.

.. code:: python

    def setup_hook(model, **kwargs):
        return kwargs

    def return_hook(model, output, **kwargs):
        output["meta"] = {"source": "api"}
        return output

    class Config:
        API_SETUP_CALLBACK = setup_hook
        API_RETURN_CALLBACK = return_hook

.. tip::

    Method-specific callbacks (e.g. ``API_GET_RETURN_CALLBACK``) override
    their global counterparts.

Custom naming conventions
-------------------------

Endpoint paths, field names and schema identifiers can be transformed to
different case styles.

.. code:: python

    class Config:
        API_ENDPOINT_CASE = "snake"
        API_FIELD_CASE = "kebab"
        API_SCHEMA_CASE = "pascal"

.. tip::

    Choose case styles that match the conventions of your existing code
    base or client applications.

