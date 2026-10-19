Extend the generated API
========================

Keep the generated routes and change only the behaviour your application needs.
Use a hook for a small adjustment, an action for a business operation, an override
for a replacement implementation, or a managed route for an unrelated endpoint.
Existing ``Meta`` configuration, callbacks, plugins and ``schema_constructor``
remain supported.

Register before initialisation
------------------------------

Create ``Architect()`` without an app, register your extensions, then call
``init_app`` inside your application context, after configuring your models.
This lets flarchitect resolve generated paths, detect conflicts and include
all the routes in OpenAPI from the start. Registration after ``init_app`` raises
a clear error. Create a separate Architect instance for each application.

.. code-block:: python

    architect = Architect()

    @architect.hook(Order, "before_create")
    def set_owner(order, context):
        order.owner_id = context.user.id
        return order

    with app.app_context():
        architect.init_app(app)

No extensions are required for ordinary CRUD. Existing ``Architect(app)`` setup
continues to work when you do not need these registrations.

Choose the smallest extension
-----------------------------

* Need different fields, roles, allowed methods or paths? Start with model
  ``Meta`` configuration.
* Need tenant or owner isolation? Use ``API_ACCESS_POLICY.scope_query`` and the
  corresponding ``can_read``, ``can_create``, ``can_update`` and ``can_delete``
  checks. Query hooks are customisation, not a replacement for access policies.
* Need to adjust a query or a record before saving? Use ``hook``.
* Need to approve an order or cancel a booking? Use ``action``.
* Need a different implementation of one CRUD operation? Use ``override``.
* Need a health endpoint or a non-model response? Use ``route``.

Hooks: keep the generated implementation
----------------------------------------

All hooks take ``(value, context)``. Return a replacement value, or return
``None`` to keep the current value after modifying it. Multiple hooks run in
registration order, after the corresponding legacy callback.

.. code-block:: python

    @architect.hook(Order, "query")
    def open_orders(query, context):
        return query.filter(Order.status == "open")

    @architect.hook(Order, "before_update")
    def check_order(order, context):
        if order.quantity < 1:
            abort(422, "Quantity must be at least one")
        return order

Available events:

* ``query``: receives the collection Query before sorting, counting and
  pagination. Access-policy scope is reapplied afterwards. It does not filter
  detail reads or mutations; use an access policy for restrictions that must
  apply everywhere.
* ``before_create``: receives the constructed record before it is saved.
* ``before_update``: receives the record with validated changes applied, before
  saving.
* ``before_delete``: receives the record before the built-in deletion.
* ``after_operation``: receives the record or list of records before
  serialisation; pagination metadata stays managed by the framework. Creates
  and updates supply the record, and actions supply their handler's return value.
  Deletion supplies the existing ``(None, 200)`` success tuple.

``after_operation`` is for response adjustments, not validation or external
side effects: ordinary generated writes have already committed at that point.
Use a before hook for validation. Extra response fields must also be declared
in your output schema.

Actions: add business logic
---------------------------

.. code-block:: python

    @architect.action(Order, "approve", methods=["POST"])
    def approve_order(order, context):
        order.approved = True
        return order

This adds ``POST /api/orders/<id>/approve`` using the model's actual path and
primary-key converter. It also follows ``API_PREFIX`` and alternate
``Meta.endpoint`` paths. Existing CRUD and relationship routes remain available.
POST is the default; GET, PATCH, PUT and DELETE are also supported. Actions are
record-level; use ``route`` for a collection-wide or unrelated operation.

The framework loads the record within the configured policy scope, checks read
access and, for writes, update access (delete access for DELETE). These policy
calls receive the action name, such as ``approve``. Authentication, role and
rate-limit settings are inherited from the model. A blocked method or read-only
model cannot gain a write endpoint through an action.

Use ``permission`` for an additional business permission; it must return a
truthy value to allow the action. It cannot bypass the model's policy checks.

.. code-block:: python

    from marshmallow import Schema, fields

    class ApprovalInput(Schema):
        reason = fields.String(required=True)

    @architect.action(
        Order,
        "approve",
        input_schema=ApprovalInput,
        roles=["manager"],
        permission=lambda order, context: order.status == "pending",
    )
    def approve_order(order, context):
        order.approval_reason = context.data["reason"]
        order.status = "approved"
        return order

Action input is not inferred from the model: declare ``input_schema`` when the
action accepts a body, then read validated values from ``context.data``. Output
defaults to the model's generated schema. Override ``output_schema`` for a
different response, or use ``output_schema=None`` for a plain dictionary.
``summary``, ``group_tag``, ``roles``, ``roles_any_of`` and ``auth`` are passed to
the existing schema wrapper. ``auth=False`` is an explicit authentication opt-out;
it does not disable access policies.

Overrides: replace one operation
--------------------------------

.. code-block:: python

    @architect.override(Order, "create")
    def create_order(data, context):
        return Order(name=data["name"].strip().upper())

Only the generated create implementation changes. Input validation, output
schema, authentication, roles, rate limits and OpenAPI stay in place. An override
applies to the model's canonical and alternate CRUD paths, not relationship
operations. Registering a second override for the same operation, or an override
for an operation that has no generated route, fails during setup.

Supported contracts:

* ``create(data, context)``: receives validated input and returns a model
  instance. The framework adds it to the session and flushes its generated ID.
* ``update(record, context)``: receives the scoped, authorised record; read the
  validated patch from ``context.data`` and apply your changes explicitly.
  Return a model instance.
* ``delete(record, context)``: receives the scoped, authorised record. Perform
  the deletion with ``context.session.delete(record)`` or implement your own
  soft delete. Return ``None``; the framework emits the standard success response.
* ``retrieve(record, context)``: receives the visible record and returns the
  value to serialise with the existing output schema.
* ``list(query, context)``: receives the generated query, after normal filters
  and query hooks, and must return a SQLAlchemy Query. Sorting, soft-delete
  filtering, counts and pagination still run afterwards. Policy scope is
  reapplied so a replacement query cannot drop it. Keep the query's model shape;
  use a managed route for reports with unrelated rows or aggregates.

Mutation overrides replace the persistence implementation, including legacy
add/update/remove callbacks. The new ``before_create`` and ``before_update``
hooks still run on the returned model. A delete override owns its own deletion
behaviour; use the built-in deletion and ``before_delete`` when you only need a
small adjustment. Generated setup/return callbacks and operation plugins remain
around the replacement operation.

Transaction ownership
---------------------

For write actions and mutation overrides, flarchitect flushes changes before
serialisation and commits only after the response is successfully constructed.
Handler exceptions, validation/serialisation errors and unsuccessful responses
roll back the session. Handlers must not commit or close the session themselves.
Use ``context.session.flush()`` when you need an ID earlier.

The transaction covers the resolved SQLAlchemy session only. External services,
email, and other databases cannot be rolled back by flarchitect. Keep durable
external work behind an outbox or your application's own delivery mechanism.
GET actions are read-only: their session is rolled back after the response.
Ordinary generated CRUD keeps its existing commit timing.

One context everywhere
----------------------

``OperationContext`` is exported from ``flarchitect`` for type annotations.
It provides ``model``, ``session``, ``operation``, ``data`` (validated input),
``user`` (the current authenticated user, possibly None) and ``request``.
Operation names are ``list``, ``retrieve``, ``create``, ``update``, ``delete``, or
an action's registered name. Context instances belong to one request.

Managed routes: one decorator
-----------------------------

.. code-block:: python

    @architect.route("/health", methods=["GET"], auth=False)
    def health():
        return {"healthy": True}

    @architect.route("/echo", methods=["POST"], input_schema=ApprovalInput)
    def echo(deserialized_data):
        return deserialized_data

Paths are full Flask paths: ``API_PREFIX`` is not added to ``route``. Use Flask
path variables as usual. ``endpoint`` sets an explicit Flask endpoint name;
remaining options go to ``schema_constructor``. Without an output schema,
dictionaries are wrapped in the normal response envelope. These routes receive
the same wrapper validation, authentication, rate limiting and documentation
as manual routes, but do not automatically load records or manage transactions.

Conflicting paths/methods raise a setup error rather than silently replacing a
route. To replace generated CRUD, use ``override``. Existing Flask blueprints
and ``@app.route`` plus ``@architect.schema_constructor`` remain available.

Runnable example
----------------

See ``demo/extensions/app.py`` for a complete in-memory application containing
a hook, action, create override and managed route. Run it from the repository:

.. code-block:: console

    python -m demo.extensions.app
    curl -X POST http://127.0.0.1:5000/api/orders \
      -H 'Content-Type: application/json' -d '{"name":"new order"}'
    curl -X POST http://127.0.0.1:5000/api/orders/1/approve
    curl http://127.0.0.1:5000/docs/apispec.json

The demonstration disables authentication for local use; configure authentication
and access policies before exposing an application to other users.
