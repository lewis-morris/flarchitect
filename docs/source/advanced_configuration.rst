Advanced Configuration
======================

When your API grows, you might need tools for shaping traffic, offloading
storage and refining responses. Beyond the basics, **flarchitect** offers
several options for these scenarios. The following sections walk through
common patterns such as rate limiting, cache configuration and response
metadata.

Initialising with optional features
-----------------------------------

``Architect.init_app`` accepts keyword arguments that toggle optional
behaviour like caching, CORS handling and automatic documentation
generation.

.. code:: python

    from flarchitect import Architect

    architect = Architect()
    architect.init_app(
        app,
        cache={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300},
        enable_cors=True,
        create_docs=True,
    )

These keywords mirror their respective ``API_*`` configuration values and
allow feature flags to be set programmatically during initialisation.

As traffic increases, managing how often clients can hit your API becomes
critical.

Full auto mode
--------------

``flarchitect`` enables automatic route creation by default. With
``FULL_AUTO = True`` the :class:`~flarchitect.Architect` scans your models at
startup and registers CRUD routes for each one. This is convenient for new
projects but may conflict with custom blueprints or hand-written views.

Disable ``FULL_AUTO`` when you need to manage routes manually or only expose a
subset of models. After turning it off you must call ``init_api`` explicitly to
register any automatic routes you still require.

.. code:: python

    app = Flask(__name__)
    app.config["FULL_AUTO"] = False
    arch = Architect(app)
    arch.init_api(app=app)  # manually trigger route generation

Use this mode when integrating with existing applications or when automatic
registration would create unwanted endpoints.

Rate limiting
-------------

Rate limits can be applied globally, per HTTP method or per model. For
example, to shield a public search endpoint from abuse, you might allow only
``100`` GET requests per minute.

**Global limit**

.. code:: python

    class Config:
        API_RATE_LIMIT = "200 per day"

**Model specific**

.. code:: python

    class Book(db.Model):
        __tablename__ = "book"

        class Meta:
            rate_limit = "5 per minute"      # becomes API_RATE_LIMIT

Because limits depend on counting requests, those counts must live
somewhere.

.. _api_caching:

Caching backends
-----------------

``flarchitect`` can cache GET responses when `API_CACHE_TYPE <configuration.html#CACHE_TYPE>`_ is set. If
``flask-caching`` is installed, any of its backends (such as Redis or
Memcached) may be used. When ``flask-caching`` is **not** available and
`API_CACHE_TYPE <configuration.html#CACHE_TYPE>`_ is ``"SimpleCache"``, a bundled
``SimpleCache`` provides an in-memory fallback. This lightweight cache is
cleared when the process restarts and stores data only for the current
worker, making it suitable for development or tests rather than
production.

Compared to ``flask-caching`` it lacks distributed backends, cache
invalidation features and the broader decorator API. For deployments with
multiple workers or where persistence matters, install ``flask-caching``
and configure a production-ready backend instead.

The rate limiter also stores counters in a cache backend. When initialising,
``flarchitect`` will automatically use a locally running Memcached,
Redis or MongoDB instance. To point to a specific backend, supply a storage
URI:

.. code:: python

    class Config:
        API_RATE_LIMIT_STORAGE_URI = "redis://redis.example.com:6379"

If no backend is available, the limiter falls back to in-memory storage
with rate-limit headers enabled by default. In production, you might point
to a shared Redis cluster so that multiple application servers enforce the
same limits.

You can also cache ``GET`` responses by choosing a backend with
`API_CACHE_TYPE <configuration.html#CACHE_TYPE>`_. When `flask-caching <https://flask-caching.readthedocs.io/>`_
is installed, set `API_CACHE_TYPE <configuration.html#CACHE_TYPE>`_ to any supported backend such as
``RedisCache``. If the extension is missing, specifying ``SimpleCache``
activates a small in-memory cache bundled with ``flarchitect``; any other
value will raise a :class:`RuntimeError`. Use `API_CACHE_TIMEOUT <configuration.html#CACHE_TIMEOUT>`_ to control
how long items remain cached.

Example ``RedisCache`` setup with a ``SimpleCache`` fallback and a cached
``GET`` request::

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

For a runnable example demonstrating cached responses see the `caching demo <https://github.com/lewis-morris/flarchitect/tree/master/demo/caching>`_.

After securing throughput, you can also shape what your clients see in each
payload.

Response metadata
-----------------

``flarchitect`` can attach additional metadata to every response. These
keys let you toggle each field individually. Including version numbers, for
example, helps client developers cache against the correct release:

.. list-table::
   :header-rows: 1

   * - Key
     - Default
     - Effect
   * - `API_DUMP_HYBRID_PROPERTIES <configuration.html#DUMP_HYBRID_PROPERTIES>`_
     - ``True``
     - Include SQLAlchemy hybrid properties in serialised output.
   * - `API_DUMP_DATETIME <configuration.html#DUMP_DATETIME>`_
     - ``True``
     - Append the current UTC timestamp as ``datetime``.
   * - `API_DUMP_VERSION <configuration.html#DUMP_VERSION>`_
     - ``True``
     - Embed the API version string as ``api_version``.
   * - `API_DUMP_STATUS_CODE <configuration.html#DUMP_STATUS_CODE>`_
     - ``True``
     - Add the HTTP status code to the payload.
   * - `API_DUMP_RESPONSE_MS <configuration.html#DUMP_RESPONSE_MS>`_
     - ``True``
     - Include elapsed processing time in milliseconds as ``response_ms``.
   * - `API_DUMP_TOTAL_COUNT <configuration.html#DUMP_TOTAL_COUNT>`_
     - ``True``
     - Provide a ``total_count`` field for collection endpoints.
   * - `API_DUMP_REQUEST_ID <configuration.html#DUMP_REQUEST_ID>`_
     - ``False``
     - Include the per-request correlation identifier as ``request_id``. The header ``X-Request-ID`` is always sent.
   * - `API_DUMP_NULL_NEXT_URL <configuration.html#DUMP_NULL_NEXT_URL>`_
     - ``True``
     - Show ``next_url`` with ``null`` when no further page exists.
   * - `API_DUMP_NULL_PREVIOUS_URL <configuration.html#DUMP_NULL_PREVIOUS_URL>`_
     - ``True``
     - Show ``previous_url`` with ``null`` when at the first page.
   * - `API_DUMP_NULL_ERRORS <configuration.html#DUMP_NULL_ERRORS>`_
     - ``True``
     - Always include an ``errors`` field, defaulting to ``null``.

Example
^^^^^^^

With metadata enabled (defaults)::

    {
        "data": [...],
        "datetime": "2024-01-01T00:00:00Z",
        "api_version": "0.0.0",
        "status_code": 200,
        "response_ms": 15,
        "total_count": 1,
        "next_url": null,
        "previous_url": null,
        "errors": null
    }

Disabling all metadata::

    class Config:
        API_DUMP_DATETIME = False
        API_DUMP_VERSION = False
        API_DUMP_STATUS_CODE = False
        API_DUMP_RESPONSE_MS = False
        API_DUMP_TOTAL_COUNT = False
        API_DUMP_NULL_NEXT_URL = False
        API_DUMP_NULL_PREVIOUS_URL = False
        API_DUMP_NULL_ERRORS = False

    {
        "data": [...]
    }

Nested model creation
---------------------

Nested writes are disabled by default. Enable them globally with

`API_ALLOW_NESTED_WRITES <configuration.html#ALLOW_NESTED_WRITES>`_ or per model via
``Meta.allow_nested_writes``.

.. code:: python

    class Config:
        API_ALLOW_NESTED_WRITES = True

    class Parent(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String)
        children = db.relationship("Child", back_populates="parent")

        class Meta:
            allow_nested_writes = True

    class Child(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String)
        parent_id = db.Column(db.Integer, db.ForeignKey("parent.id"))
        parent = db.relationship("Parent", back_populates="children")

        class Meta:
            allow_nested_writes = True

With this configuration a nested object can be created in the same request::

    POST /api/parent
    {
        "name": "Jane",
        "children": [{"name": "Junior"}]
    }

Depth limits
^^^^^^^^^^^^

Once enabled, ``AutoSchema`` can deserialise nested relationship data during
``POST`` or ``PUT`` requests. Each related model must also opt in with
``Meta.allow_nested_writes`` and nesting is capped at **two levels** to avoid
unbounded recursion. Any relationships beyond this depth are ignored.

Validation errors
^^^^^^^^^^^^^^^^^

Errors raised within nested objects bubble up under their relationship path.
In the following request, the invalid email on the ``author`` is reported in
the error response::

    POST /api/book
    {
        "title": "My Book",
        "author": {"email": "not-an-email"}
    }

    {
        "errors": {"author": {"email": ["Not a valid email address."]}}
    }

Example: multiple nested levels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With nested writes enabled you can create several related objects at once,
up to two levels deep::

    {
        "title": "My Book",
        "isbn": "12345",
        "publication_date": "2024-01-01",
        "author": {
            "first_name": "John",
            "last_name": "Doe",
            "publisher": {
                "name": "Acme Publishing"
            }
        }
    }

To partially update a nested relationship, send only the fields you want to
change in a ``PATCH`` request::

    PATCH /books/1
    {
        "author": {
            "id": 1,
            "biography": "Updated bio"
        }
    }

The nested ``author`` object is deserialised into an ``Author`` instance while
responses continue to use the configured serialisation type (URL, JSON, or
dynamic).


.. _soft-delete:

Soft delete
-----------

``flarchitect`` can mark records as deleted without removing them from the
database. This allows you to hide data from normal queries while retaining it
for auditing or future restoration.

Configuration
^^^^^^^^^^^^^

Enable soft deletes and define how records are flagged:

.. code-block:: python

   class Config:
       API_SOFT_DELETE = True
       API_SOFT_DELETE_ATTRIBUTE = "deleted"
       API_SOFT_DELETE_VALUES = (False, True)

`API_SOFT_DELETE_ATTRIBUTE <configuration.html#SOFT_DELETE_ATTRIBUTE>`_ names the column that stores the deleted flag.
`API_SOFT_DELETE_VALUES <configuration.html#SOFT_DELETE_VALUES>`_ is a tuple where the first value represents an
active record and the second marks it as deleted.

Example model
^^^^^^^^^^^^^

Add a boolean column to your base model so every table can inherit the flag:

.. code-block:: python

   from datetime import datetime
   from flask_sqlalchemy import SQLAlchemy
   from sqlalchemy import Boolean, DateTime
   from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

   class BaseModel(DeclarativeBase):
       created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
       updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
       deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

   db = SQLAlchemy(model_class=BaseModel)

   class Book(db.Model):
       __tablename__ = "books"
       id: Mapped[int] = mapped_column(primary_key=True)
       title: Mapped[str] = mapped_column()

Example queries
^^^^^^^^^^^^^^^

Soft deleted rows are hidden from normal requests:

.. code-block:: http

   GET /api/books        # returns rows where deleted=False

Include the ``include_deleted`` query parameter to return all rows:

.. code-block:: http

   GET /api/books?include_deleted=true

Issuing a DELETE request marks the record as deleted. To remove it
permanently, supply ``cascade_delete=1``:

.. code-block:: http

   DELETE /api/books/1             # sets deleted=True
   DELETE /api/books/1?cascade_delete=1  # removes row from database

CORS
----

To enable `Cross-Origin Resource Sharing (CORS) <https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS>`_
for your API, set `API_ENABLE_CORS <configuration.html#ENABLE_CORS>`_ to ``True`` in the application
configuration. When active, CORS headers are applied to matching routes
defined in ``CORS_RESOURCES``.

``CORS_RESOURCES`` accepts a mapping of URL patterns to their respective
options, mirroring the format used by `Flask-CORS <https://flask-cors.readthedocs.io/>`_.

.. code:: python

    class Config:
        API_ENABLE_CORS = True
        CORS_RESOURCES = {
            r"/api/*": {"origins": "*"}
        }

If ``flask-cors`` is installed, these settings are passed through to that
extension. Without it, ``flarchitect`` compiles the patterns in
``CORS_RESOURCES`` and adds an ``Access-Control-Allow-Origin`` header for
matching requests. Only origin checking is performed; other CORS headers are
left untouched.

``flask-cors``\ -free minimal configuration::

    class Config:
        API_ENABLE_CORS = True
        CORS_RESOURCES = {r"/api/*": {"origins": ["https://example.com"]}}

Example
^^^^^^^

The following snippet enables CORS for all API routes::

    from flask import Flask
    from flarchitect import Architect

    app = Flask(__name__)
    app.config["API_ENABLE_CORS"] = True
    app.config["CORS_RESOURCES"] = {r"/api/*": {"origins": "*"}}

    architect = Architect(app)

    if __name__ == "__main__":
        app.run()

See the :doc:`configuration <configuration>` page for the full list of
available CORS settings.

Query parameter controls
------------------------

``flarchitect`` can expose several query parameters that let clients tailor
responses. These toggles may be disabled to enforce fixed behaviour.

Filtering
^^^^^^^^^

The `API_ALLOW_FILTERS <configuration.html#ALLOW_FILTERS>`_ flag enables a ``filter`` query parameter for
constraining results. For example::

    GET /api/books?filter=author_id__eq:1

Ordering
^^^^^^^^

Activate `API_ALLOW_ORDER_BY <configuration.html#ALLOW_ORDER_BY>`_ to allow sorting via ``order_by``::

    GET /api/books?order_by=-published_date

Selecting fields
^^^^^^^^^^^^^^^^

`API_ALLOW_SELECT_FIELDS <configuration.html#ALLOW_SELECT_FIELDS>`_ lets clients whitelist response columns with
the ``fields`` parameter::

    GET /api/books?fields=title,author_id

See :doc:`configuration <configuration>` for detailed descriptions of
`API_ALLOW_FILTERS <configuration.html#ALLOW_FILTERS>`_, `API_ALLOW_ORDER_BY <configuration.html#ALLOW_ORDER_BY>`_ and
`API_ALLOW_SELECT_FIELDS <configuration.html#ALLOW_SELECT_FIELDS>`_.

Joining related resources
^^^^^^^^^^^^^^^^^^^^^^^^^

Enable `API_ALLOW_JOIN <configuration.html#ALLOW_JOIN>`_ to allow clients to join related models using
the ``join`` query parameter::

    GET /api/books?join=author&fields=books.title,author.first_name

Grouping and aggregation
^^^^^^^^^^^^^^^^^^^^^^^^

`API_ALLOW_GROUPBY <configuration.html#ALLOW_GROUPBY>`_ enables the ``groupby`` parameter for SQL
``GROUP BY`` clauses. Use `API_ALLOW_AGGREGATION <configuration.html#ALLOW_AGGREGATION>`_ alongside it to
compute aggregates. Aggregates are expressed by appending a label and
function to a field name::

    GET /api/books?groupby=author_id&id|book_count__count=1

.. _cascade-deletes:

Cascade deletes
---------------

When removing a record, related rows may block the operation. These
settings let ``flarchitect`` clean up relationships automatically when
explicitly requested.

`API_ALLOW_CASCADE_DELETE <configuration.html#ALLOW_CASCADE_DELETE>`_ permits clients to trigger cascading
removal by adding ``?cascade_delete=1`` to the request. Without this
flag or query parameter, deletes that would orphan related records raise
``409 Conflict`` instead of proceeding::

    DELETE /api/books/1?cascade_delete=1

.. code-block:: python

    class Config:
        API_ALLOW_CASCADE_DELETE = True

`API_ALLOW_DELETE_RELATED <configuration.html#ALLOW_DELETE_RELATED>`_ governs whether child objects referencing
the target can be removed automatically. Disable it to require manual
cleanup of related rows:

.. code-block:: python

    class Book(db.Model):
        class Meta:
            delete_related = False  # API_ALLOW_DELETE_RELATED

`API_ALLOW_DELETE_DEPENDENTS <configuration.html#ALLOW_DELETE_DEPENDENTS>`_ covers dependent objects such as
association table entries. Turning it off forces clients to delete those
records explicitly:

.. code-block:: python

    class Book(db.Model):
        class Meta:
            delete_dependents = False  # API_ALLOW_DELETE_DEPENDENTS

See :doc:`configuration <configuration>` for default values and additional
context on these options.

Case conventions
----------------

``flarchitect`` can reshape field and schema names to match different
case conventions. These options keep the API's payloads, schemas and
endpoints consistent with the style used by your clients.

`API_FIELD_CASE <configuration.html#FIELD_CASE>`_
^^^^^^^^^^^^^^^^^^

Controls the casing for fields in JSON responses. By default, field names
use ``snake`` case. Setting `API_FIELD_CASE <configuration.html#FIELD_CASE>`_ changes the output to match
other naming styles:

.. code-block:: python

    class Config:
        API_FIELD_CASE = "camel"

.. code-block:: json

    {
        "statusCode": 200,
        "value": {
            "publicationDate": "2024-05-10"
        }
    }

Switching to ``kebab`` case instead renders the same field as
``publication-date``. Supported options include ``snake``, ``camel``,
``pascal``, ``kebab`` and ``screaming_snake``.

`API_SCHEMA_CASE <configuration.html#SCHEMA_CASE>`_
^^^^^^^^^^^^^^^^^^^

Defines the naming convention for generated schema names in the OpenAPI
document. The default, ``camel``, produces schema identifiers such as
``apiCalls``. Other styles are also available:

.. code-block:: python

    class Config:
        API_SCHEMA_CASE = "screaming_snake"

Interplay with `API_ENDPOINT_CASE <configuration.html#ENDPOINT_CASE>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`API_ENDPOINT_CASE <configuration.html#ENDPOINT_CASE>`_ controls the casing of the generated URL paths. To
maintain a consistent style across paths, schemas and payloads, combine
`API_ENDPOINT_CASE <configuration.html#ENDPOINT_CASE>`_ with the appropriate `API_FIELD_CASE <configuration.html#FIELD_CASE>`_ and
`API_SCHEMA_CASE <configuration.html#SCHEMA_CASE>`_ values. For example, selecting ``kebab`` endpoint
casing pairs naturally with ``kebab`` field names.


.. _advanced-extensions:

Extensions, validators and hooks
-------------------------------

``flarchitect`` offers several extension points for tailoring behaviour beyond
configuration files. These hooks let you alter request handling, apply
additional field validation and tweak responses on a per-route basis.

Response callbacks
^^^^^^^^^^^^^^^^^^

Return callbacks run after database operations but before the response is
serialised. Use them to adjust the output or append metadata.

.. code-block:: python

    from datetime import datetime

    def add_timestamp(model, output, **kwargs):
        output["generated"] = datetime.utcnow().isoformat()
        return {"output": output}

    class Config:
        API_RETURN_CALLBACK = add_timestamp

See :func:`flarchitect.core.routes.create_route_function` for details on how
responses are constructed.

Custom validators
^^^^^^^^^^^^^^^^^


Attach validators to SQLAlchemy columns via the ``info`` mapping.
Validators are looked up in :mod:`flarchitect.schemas.validators` and
applied automatically.

.. code-block:: python

    class User(db.Model):
        email = db.Column(
            db.String,
            info={"validator": "email", "validator_message": "Invalid email"},
        )

See :doc:`validation` for the full list of available validators.

Per-route hooks
^^^^^^^^^^^^^^^

Execute custom logic before or after a specific route by defining setup or
return callbacks in configuration or on a model's ``Meta`` class.

.. code-block:: python

    from flask import abort
    from flask_login import current_user

    def ensure_admin(model, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return kwargs

    class Book(db.Model):
        class Meta:
            return_callback = add_timestamp

    class Config:
        API_SETUP_CALLBACK = ensure_admin

For more examples see the :doc:`extensions` page.
