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
