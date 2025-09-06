Extensions
=========================================

Callbacks let you hook into the request lifecycle to run custom logic around
database operations and responses. They can be declared globally in the Flask
configuration or on individual SQLAlchemy models.

.. note::

   With ``AUTO_NAME_ENDPOINTS`` enabled (the default), flarchitect generates a
   summary for each endpoint based on its schema and HTTP method. Disable this
   flag if your callbacks provide custom summaries to prevent them from being
   overwritten.

Request lifecycle and hook order
--------------------------------

This is the high‑level order in which flarchitect processes a request and where
each callback/plugin hook sits. Understanding the flow helps you choose the
right extension point and the available context.

1) ``request_started`` plugin hook
   - Called at the very beginning of the request (``@app.before_request``).
   - Signature: ``request_started(request: flask.Request) -> None``.

2) Authentication
   - For routes not wrapped by ``schema_constructor``, global auth runs via
     ``Architect._global_authentication``.
   - For ``schema_constructor`` routes, auth runs inside the wrapper before
     schemas and rate limiting are applied.
   - Plugin hooks around auth:
     - ``before_authenticate(context: dict) -> dict | None`` – may update context.
     - ``after_authenticate(context: dict, success: bool, user: Any | None) -> None``.
   - ``context`` keys: ``model`` (type | None), ``method`` (str), optionally
     ``output_schema`` / ``input_schema``.

3) Route execution (``schema_constructor`` routes)
   a. Plugin ``before_model_op``
      - Called with a rich context before any model operation. Return a dict to
        merge into context/kwargs.
   b. Global/Model callbacks in order:
      - ``API_GLOBAL_SETUP_CALLBACK`` (method‑aware) → may mutate kwargs
      - ``API_SETUP_CALLBACK`` (method‑aware) → may mutate kwargs
   c. CRUD service action runs (get/add/update/delete)
      - Internally may call:
        - ``API_FILTER_CALLBACK(query, model, params)`` to adjust the query
        - ``API_ADD_CALLBACK(obj, model)`` before commit on POST
        - ``API_UPDATE_CALLBACK(obj, model)`` before commit on PATCH
        - ``API_REMOVE_CALLBACK(obj, model)`` before delete/soft‑delete on DELETE
   d. ``API_RETURN_CALLBACK`` (method‑aware) → adjust/replace action output
   e. Plugin ``after_model_op`` (may replace the output)

4) Response wrapping and serialisation
   - Marshmallow dump occurs inside the ``schema_constructor`` wrapper. After
     Marshmallow serialises data, ``API_DUMP_CALLBACK(data, **kwargs)`` runs.
   - The final payload is wrapped by ``create_response`` to a standard JSON
     envelope. Before the response is serialised, ``API_FINAL_CALLBACK`` can
     mutate the response dictionary.
   - Errors (raised exceptions or error statuses) trigger ``API_ERROR_CALLBACK``.

5) ``request_finished`` plugin hook
   - Runs in ``@app.after_request``. May return a replacement ``Response``.
   - Signature: ``request_finished(request: flask.Request, response: flask.Response) -> flask.Response | None``.

Callback types
--------------

flarchitect recognises a number of callback hooks that allow you to run custom
logic at various stages of processing:

* **Global setup** – runs before any model-specific processing. ``GLOBAL_SETUP_CALLBACK`` (global: `API_GLOBAL_SETUP_CALLBACK <configuration.html#GLOBAL_SETUP_CALLBACK>`_)
* **Setup** – runs before database operations. Useful for validation, logging
  or altering incoming data. ``SETUP_CALLBACK`` (global: `API_SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>`_)
* **Filter** – lets you adjust the SQLAlchemy query object before filtering and
  pagination are applied. ``FILTER_CALLBACK`` (global: `API_FILTER_CALLBACK <configuration.html#FILTER_CALLBACK>`_)
* **Add** – called before a new object is committed to the database. ``ADD_CALLBACK`` (global: `API_ADD_CALLBACK <configuration.html#ADD_CALLBACK>`_)
* **Update** – invoked prior to persisting updates to an existing object. ``UPDATE_CALLBACK`` (global: `API_UPDATE_CALLBACK <configuration.html#UPDATE_CALLBACK>`_)
* **Remove** – executed before an object is deleted. ``REMOVE_CALLBACK`` (global: `API_REMOVE_CALLBACK <configuration.html#REMOVE_CALLBACK>`_)
* **Return** – runs after the database operation but before the response is
  returned. Ideal for adjusting the output or adding headers. ``RETURN_CALLBACK`` (global: `API_RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>`_)
* **Dump** – executes after Marshmallow serialisation allowing you to modify
  the dumped data. ``DUMP_CALLBACK`` (global: `API_DUMP_CALLBACK <configuration.html#DUMP_CALLBACK>`_)
* **Final** – runs immediately before the response is sent to the client. ``FINAL_CALLBACK`` (global: `API_FINAL_CALLBACK <configuration.html#FINAL_CALLBACK>`_)
* **Error** – triggered when an exception bubbles up; handle logging or
  notifications here. ``ERROR_CALLBACK`` (global: `API_ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>`_)

Configuration
-------------

Callbacks are referenced by the following configuration keys (global variants
use ``API_<KEY>``):

* ``GLOBAL_SETUP_CALLBACK`` / `API_GLOBAL_SETUP_CALLBACK <configuration.html#GLOBAL_SETUP_CALLBACK>`_
* ``SETUP_CALLBACK`` / `API_SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>`_
* ``FILTER_CALLBACK`` / `API_FILTER_CALLBACK <configuration.html#FILTER_CALLBACK>`_
* ``ADD_CALLBACK`` / `API_ADD_CALLBACK <configuration.html#ADD_CALLBACK>`_
* ``UPDATE_CALLBACK`` / `API_UPDATE_CALLBACK <configuration.html#UPDATE_CALLBACK>`_
* ``REMOVE_CALLBACK`` / `API_REMOVE_CALLBACK <configuration.html#REMOVE_CALLBACK>`_
* ``RETURN_CALLBACK`` / `API_RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>`_
* ``DUMP_CALLBACK`` / `API_DUMP_CALLBACK <configuration.html#DUMP_CALLBACK>`_
* ``FINAL_CALLBACK`` / `API_FINAL_CALLBACK <configuration.html#FINAL_CALLBACK>`_
* ``ERROR_CALLBACK`` / `API_ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>`_

You can apply these keys in several places:

1. **Global Flask config**

   Use ``API_<KEY>`` to apply a callback to all endpoints.

   .. code-block:: python

      class Config:
          API_SETUP_CALLBACK = my_setup

2. **Model config**

   Set lowercase attributes on a model's ``Meta`` class to apply callbacks to
   all endpoints for that model.

   .. code-block:: python

      class Author(db.Model):
          class Meta:
              setup_callback = my_setup

3. **Model method config**

   Use ``<method>_<key>`` on the ``Meta`` class for the highest level of
   specificity.

   .. code-block:: python

      class Author(db.Model):
          class Meta:
              get_return_callback = my_get_return

Callback signatures
-------------------

Setup, Global setup and filter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Setup‑style callbacks receive ``model`` and a set of keyword arguments
describing the operation. They must return a dict (possibly empty) which will
be merged into the route's processing context.

Common ``**kwargs`` keys (availability depends on the route):
- ``id``: int | str | None – primary key value for single‑item routes
- ``field``: str | None – alternative lookup field name when configured
- ``join_model``: type | None – relationship model for relation routes
- ``output_schema``: marshmallow.Schema | None – response schema
- ``relation_name``: str | None – relation attribute name (relation routes)
- ``deserialized_data``: dict | None – request body deserialised by the input schema
- ``many``: bool – whether the route returns a collection
- ``method``: str – HTTP method (e.g., "GET")
Return value: ``dict[str, Any]`` to merge back into kwargs.

Examples:
.. code-block:: python

    def my_setup_callback(model, **kwargs):
        # modify kwargs as needed
        return kwargs

    def my_filter_callback(query, model, params):
        return query.filter(model.id > 0)

Add, update and remove
^^^^^^^^^^^^^^^^^^^^^^

These callbacks receive the SQLAlchemy object instance and must return it:

.. code-block:: python

    def my_add_callback(obj, model):
        obj.created_by = "system"
        return obj

Return
^^^^^^

Return callbacks receive ``model``, ``output`` and ``**kwargs`` (same keys as
Setup). They must return a dict containing the ``output`` key. The callback can
wrap or transform the output. Typical shapes for ``output`` are:
- GET many: ``{"query": list[Model], "limit": int, "page": int, "total_count": int}``
- GET one: ``{"query": Model}``
- POST/PATCH: the created/updated model instance or a result dict
- DELETE: ``(None, 200)`` when soft‑delete/OK

.. code-block:: python

    def my_return_callback(model, output, **kwargs):
        return {"output": output}

Dump
^^^^

Dump callbacks accept ``data`` and ``**kwargs`` and must return the data:

.. code-block:: python

    def my_dump_callback(data, **kwargs):
        data["name"] = data["name"].upper()
        return data

Final
^^^^^

Final callbacks receive the response dictionary before it is serialised:

.. code-block:: python

    def my_final_callback(data):
        data["processed"] = True
        return data

Error
^^^^^

Error callbacks receive the error message, status code and a value payload
constructed by the response wrapper. Use this to send notifications or add
structured logs.

.. code-block:: python

    def my_error_callback(error, status_code, value):
        log_exception(error)

Plugin hooks
------------

Plugins provide a structured way to observe and influence behaviour across the
app. Configure with ``API_PLUGINS`` as a list of classes/instances/factories
deriving from ``flarchitect.plugins.PluginBase``.

Available hooks and signatures:
- ``request_started(request: flask.Request) -> None``
- ``request_finished(request: flask.Request, response: flask.Response) -> flask.Response | None``
- ``before_authenticate(context: dict[str, Any]) -> dict[str, Any] | None``
  - Context keys: ``model`` (type | None), ``method`` (str), optional
    ``output_schema`` / ``input_schema``.
- ``after_authenticate(context: dict[str, Any], success: bool, user: Any | None) -> None``
- ``before_model_op(context: dict[str, Any]) -> dict[str, Any] | None``
  - Context keys mirror Setup kwargs, plus ``method`` (str) and ``many`` (bool).
- ``after_model_op(context: dict[str, Any], output: Any) -> Any | None``
- ``spec_build_started(spec: Any) -> None``
- ``spec_build_completed(spec_dict: dict[str, Any]) -> dict[str, Any] | None``

Example plugin:

.. code-block:: python

   from flarchitect.plugins import PluginBase

   class AuditPlugin(PluginBase):
       def before_model_op(self, context):
           # attach correlation fields
           return {"audit": {"path": context.get("relation_name"), "method": context["method"]}}

       def after_model_op(self, context, output):
           # inject audit trail into result dicts
           if isinstance(output, dict):
               out = dict(output)
               out["audit"] = context.get("audit")
               return out
           return None

Extending query parameters
--------------------------

Use `ADDITIONAL_QUERY_PARAMS <configuration.html#ADDITIONAL_QUERY_PARAMS>`_ to document extra query parameters introduced in
a return callback. The value is a list of OpenAPI parameter objects.

.. code-block:: python

    class Config:
        API_ADDITIONAL_QUERY_PARAMS = [{
            "name": "log",
            "in": "query",
            "description": "Log call into the database",
            "schema": {"type": "string"},
        }]

    class Author(db.Model):
        class Meta:
            get_additional_query_params = [{
                "name": "log",
                "in": "query",
                "schema": {"type": "string"},
            }]

Acceptable types
----------------

``schema.type`` may be one of:

* ``string``
* ``number``
* ``integer``
* ``boolean``
* ``array``
* ``object``

Acceptable formats
------------------

Common ``schema.format`` values include:

* ``date``
* ``date-time``
* ``password``
* ``byte``
* ``binary``
* ``email``
* ``phone``
* ``postal_code``
* ``uuid``
* ``uri``
* ``hostname``
* ``ipv4``
* ``ipv6``
* ``int32``
* ``int64``
* ``float``
* ``double``

For comprehensive configuration details see :doc:`configuration`.
