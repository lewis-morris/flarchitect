Advanced Configuration
======================

Beyond the basics, **flarchitect** offers several advanced options for fine-
tuning API behaviour. This guide covers rate limiting and cache configuration.

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

Response metadata
-----------------

``flarchitect`` can attach additional metadata to every response. These
keys let you toggle each field individually:

.. list-table::
   :header-rows: 1

   * - Key
     - Default
     - Effect
   * - ``API_DUMP_HYBRID_PROPERTIES``
     - ``True``
     - Include SQLAlchemy hybrid properties in serialized output.
   * - ``API_DUMP_DATETIME``
     - ``True``
     - Append the current UTC timestamp as ``datetime``.
   * - ``API_DUMP_VERSION``
     - ``True``
     - Embed the API version string as ``api_version``.
   * - ``API_DUMP_STATUS_CODE``
     - ``True``
     - Add the HTTP status code to the payload.
   * - ``API_DUMP_RESPONSE_MS``
     - ``True``
     - Include elapsed processing time in milliseconds as ``response_ms``.
   * - ``API_DUMP_TOTAL_COUNT``
     - ``True``
     - Provide a ``total_count`` field for collection endpoints.
   * - ``API_DUMP_NULL_NEXT_URL``
     - ``True``
     - Show ``next_url`` with ``null`` when no further page exists.
   * - ``API_DUMP_NULL_PREVIOUS_URL``
     - ``True``
     - Show ``previous_url`` with ``null`` when at the first page.
   * - ``API_DUMP_NULL_ERRORS``
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

The :data:`API_ALLOW_FILTER` flag enables a ``filter`` query parameter for
constraining results. For example::

    GET /api/books?filter=author_id__eq:1

Ordering
^^^^^^^^

Activate :data:`API_ALLOW_ORDER_BY` to allow sorting via ``order_by``::

    GET /api/books?order_by=-published_date

Selecting fields
^^^^^^^^^^^^^^^^

:data:`API_ALLOW_SELECT_FIELDS` lets clients whitelist response columns with
the ``fields`` parameter::

    GET /api/books?fields=title,author_id

See :doc:`configuration <configuration>` for detailed descriptions of
:data:`API_ALLOW_FILTER`, :data:`API_ALLOW_ORDER_BY` and
:data:`API_ALLOW_SELECT_FIELDS`.

Joining related resources
^^^^^^^^^^^^^^^^^^^^^^^^^

Enable :data:`API_ALLOW_JOIN` to allow clients to join related models using
the ``join`` query parameter::

    GET /api/books?join=author&fields=books.title,author.first_name

Grouping and aggregation
^^^^^^^^^^^^^^^^^^^^^^^^

:data:`API_ALLOW_GROUPBY` enables the ``groupby`` parameter for SQL
``GROUP BY`` clauses. Use :data:`API_ALLOW_AGGREGATION` alongside it to
compute aggregates. Aggregates are expressed by appending a label and
function to a field name::

    GET /api/books?groupby=author_id&id|book_count__count=1

.. _cascade-deletes:

Cascade deletes
---------------

When removing a record, related rows may block the operation. These
settings let ``flarchitect`` clean up relationships automatically when
explicitly requested.

:data:`API_ALLOW_CASCADE_DELETE` permits clients to trigger cascading
removal by adding ``?cascade_delete=1`` to the request. Without this
flag or query parameter, deletes that would orphan related records raise
``409 Conflict`` instead of proceeding::

    DELETE /api/books/1?cascade_delete=1

.. code-block:: python

    class Config:
        API_ALLOW_CASCADE_DELETE = True

:data:`API_ALLOW_DELETE_RELATED` governs whether child objects referencing
the target can be removed automatically. Disable it to require manual
cleanup of related rows:

.. code-block:: python

    class Book(db.Model):
        class Meta:
            delete_related = False  # API_ALLOW_DELETE_RELATED

:data:`API_ALLOW_DELETE_DEPENDENTS` covers dependent objects such as
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

``API_FIELD_CASE``
^^^^^^^^^^^^^^^^^^

Controls the casing for fields in JSON responses. By default, field names
use ``snake`` case. Setting ``API_FIELD_CASE`` changes the output to match
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

``API_SCHEMA_CASE``
^^^^^^^^^^^^^^^^^^^

Defines the naming convention for generated schema names in the OpenAPI
document. The default, ``camel``, produces schema identifiers such as
``apiCalls``. Other styles are also available:

.. code-block:: python

    class Config:
        API_SCHEMA_CASE = "screaming_snake"

.. code-block:: json

    {
        "components": {
            "schemas": {
                "API_CALLS": {
                    "...": "..."
                }
            }
        }
    }

Interplay with ``API_ENDPOINT_CASE``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``API_ENDPOINT_CASE`` controls the casing of the generated URL paths. To
maintain a consistent style across paths, schemas and payloads, combine
``API_ENDPOINT_CASE`` with the appropriate ``API_FIELD_CASE`` and
``API_SCHEMA_CASE`` values. For example, selecting ``kebab`` endpoint
casing pairs naturally with ``kebab`` field names.


.. _advanced-callbacks:

Callbacks, validators and hooks
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
        API_GET_RETURN_CALLBACK = add_timestamp

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
            post_return_callback = add_timestamp

    class Config:
        API_POST_SETUP_CALLBACK = ensure_admin

For more examples see the :doc:`callbacks` page.

