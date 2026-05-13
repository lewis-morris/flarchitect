Manual Routes
=========================================

flarchitect can wrap your own Flask view functions with the same machinery it
uses for generated endpoints. This is helpful when you hand‑craft a route but
still want consistent authentication, schema validation/serialisation, rate
limiting and OpenAPI documentation.

Use ``architect.schema_constructor`` to decorate a view and describe how it
should be treated. The decorator applies input/output Marshmallow schemas,
honours auth/roles config, attaches rate limiting, and registers the route for
documentation generation.

Reserving canonical paths
-------------------------

By default *flarchitect* registers RESTful collection/detail routes for every
model under the canonical prefix (for example ``/api/orders`` and
``/api/orders/<id>``). Projects that need bespoke logic for those URLs can turn
the automatic routes off while still relying on auto-generated schemas,
relations and alternate endpoints.

- Disable the feature globally with
  ``API_REGISTER_CANONICAL_ROUTES = False``.
- Override per model via ``Meta.register_canonical_routes = False``.
- Supply alternate auto-generated endpoints with ``Meta.endpoint`` (string or
  list) so CRUD handlers remain available under a different prefix.

Example::

    class Config:
        API_REGISTER_CANONICAL_ROUTES = False  # keep /api/v1/orders for bespoke handlers

    class Order(db.Model):
        __tablename__ = "orders"

        class Meta:
            tag = "Order"
            register_canonical_routes = False
            endpoint = "orders/records"  # auto CRUD lives here instead

    @app.get("/api/v1/orders")
    def bespoke_orders():
        """Your custom collection handler."""
        ...

The default remains ``True`` so existing projects keep their canonical routes
until they opt out. Relation endpoints and discovery continue to work because
the underlying services are still created.

Basic usage
-----------

.. code-block:: python

   from flask import Flask
   from marshmallow import Schema, fields
   from flarchitect import Architect

   app = Flask(__name__)
   app.config.update(
       API_TITLE="My API",
       API_VERSION="1.0",
       # Enable JWT (or your chosen method) if you want auth enforced
       API_AUTHENTICATE_METHOD=["jwt"],
   )

   architect = Architect(app)

   class HelloOut(Schema):
       message = fields.String(required=True)

   @app.get("/hello")
   @architect.schema_constructor(
       output_schema=HelloOut,   # serialise the return value with this schema
       group_tag="Custom",       # group in docs
       auth=True,                # enforce configured auth on this route
   )
   def hello():
       return {"message": "world"}

The decorator automatically:

- Validates/serialises using the provided schemas.
- Enforces authentication (unless ``auth=False`` is set).
- Applies any configured rate limit (see ``API_RATE_LIMIT`` and model/method overrides).
- Registers the route so it appears in the OpenAPI spec and docs.

Input and output schemas
------------------------

You can validate request bodies and serialise responses with Marshmallow
schemas. Use ``input_schema`` for inbound data and ``output_schema`` for the
response. For endpoints returning a list, pass ``many=True`` to control how
serialisation is applied.

If you don't want flarchitect to serialise the response, set
``output_schema=None``. In this mode the wrapper skips field selection and
Marshmallow dumping entirely and your handler's return value (dict or list)
is wrapped unchanged in the standard JSON envelope.

.. code-block:: python

   class ItemIn(Schema):
       name = fields.String(required=True)

   class ItemOut(Schema):
       id = fields.Integer(required=True)
       name = fields.String(required=True)

   @app.post("/items")
   @architect.schema_constructor(input_schema=ItemIn, output_schema=ItemOut)
   def create_item():
       # Access validated input via Flask's request.json in your handler
       ...
       return {"id": 1, "name": "example"}

Route handler signature
-----------------------

Decorated handlers may optionally accept ``deserialized_data`` to receive the
validated request body when ``input_schema`` is provided. Extra wrapper kwargs
such as ``model`` are filtered and only arguments declared in your function
signature are passed, so both of the following are valid:

.. code-block:: python

   @app.post("/echo")
   @architect.schema_constructor(input_schema=ItemIn, output_schema=None)
   def echo(deserialized_data=None):
       return deserialized_data

   # or
   @app.post("/echo2")
   @architect.schema_constructor(input_schema=ItemIn, output_schema=None)
   def echo2(deserialized_data=None, **kwargs):  # kwargs may include 'model'
       return deserialized_data

Roles and authentication
------------------------

If your application uses role‑based access control, supply ``roles`` to require
users to have specific roles on this route. By default, when authentication is
enabled globally, roles are enforced automatically for decorated routes.

.. code-block:: python

   @app.get("/admin/stats")
   @architect.schema_constructor(output_schema=HelloOut, roles=["admin"])  # require the "admin" role
   def admin_stats():
       return {"message": "ok"}

To allow access when the user has any of multiple roles, either set
``roles_any_of=True`` or pass a dict with ``{"roles": [...], "any_of": True}``:

.. code-block:: python

   @app.get("/content/edit")
   @architect.schema_constructor(output_schema=HelloOut, roles=["editor", "admin"], roles_any_of=True)
   def edit_content():
       return {"message": "ok"}

   # equivalent
   @app.get("/content/edit-alt")
   @architect.schema_constructor(output_schema=HelloOut, roles={"roles": ["editor", "admin"], "any_of": True})
   def edit_content_alt():
       return {"message": "ok"}

To opt out of authentication for a specific manual route, set ``auth=False``:

.. code-block:: python

   @app.get("/public/ping")
   @architect.schema_constructor(output_schema=HelloOut, auth=False)
   def public_ping():
       return {"message": "pong"}

Alternatively, configure ``API_AUTH_REQUIREMENTS`` to opt HTTP verbs or route
flavours in/out of authentication at the config level. Manual routes decorated
with ``schema_constructor`` honour the map—use it to make every ``GET`` route
public, for instance, without adding ``auth=False`` repeatedly. Apply
``API_ACCESS_POLICY`` when you need row-level checks so both generated and
manual endpoints share the same access logic.
When working with cookie-based credentials, combine ``API_AUTH_TOKEN_PROVIDERS``
(for example ``['cookie', 'header']``) with the
``load_user_from_cookie`` helper to populate ``current_user`` outside the
standard auth flow. Use :func:`flarchitect.utils.cookie_settings` to retrieve
project-aligned cookie keyword arguments (merged from ``API_COOKIE_DEFAULTS``
and ``SESSION_COOKIE_*``) whenever you issue or clear cookies.

Documentation metadata
----------------------

``schema_constructor`` records metadata so your manual routes show up in the
OpenAPI document and UI. Useful kwargs include:

- ``group_tag``: Group name used for sectioning in docs.
- ``summary``: Short summary for the operation.
- ``tag``: Additional tag label if needed.
- ``error_responses``: Mapping of error codes to descriptions used in docs.

Additional helpers
------------------

If you only need to protect a manual route with JWT and don’t require schema
wrapping or documentation, you can use ``jwt_authentication`` directly:

.. code-block:: python

   from flarchitect.core.architect import jwt_authentication

   @app.get("/profile")
   @jwt_authentication
   def profile():
       return {"status": "ok"}

This decorator validates the ``Authorization: Bearer <token>`` header and sets
the current user context.
