Plugins
=======

flarchitect supports a lightweight plugin system for observing and customising
behaviour at well-defined hook points. Use plugins for cross-cutting concerns
such as auditing, metrics, tenant scoping, or output shaping that shouldn’t
live in route handlers.

Quick start
-----------

1. Implement a plugin by subclassing ``flarchitect.plugins.PluginBase``::

    from flarchitect.plugins import PluginBase

    class AuditPlugin(PluginBase):
        def before_model_op(self, context):
            # e.g. attach actor/tenant to the payload
            data = context.get("deserialized_data") or {}
            if isinstance(data, dict):
                data = {**data, "actor": context.get("request_id")}
                return {"deserialized_data": data}

        def after_model_op(self, context, output):
            # e.g. emit an audit log
            print("AUDIT:", context.get("method"), context.get("model"), output)

2. Register your plugin via Flask config::

    app.config["API_PLUGINS"] = [AuditPlugin()]

Hook reference
--------------

Stable hook signatures (kwargs may grow over time):

- request_started(request: flask.Request) -> None
    Called at the beginning of each request.

- request_finished(request: flask.Request, response: flask.Response) -> flask.Response | None
    Called after a response is created. Return a replacement Response to override.

- before_authenticate(context: dict) -> dict | None
    Runs prior to authentication (for non-schema routes and schema routes alike).
    May return a dict of updates to merge into the context.

- after_authenticate(context: dict, success: bool, user: Any | None) -> None
    Runs after authentication attempt.

- before_model_op(context: dict) -> dict | None
    Runs before a CRUD action. Context includes keys such as ``model``, ``method``,
    ``many``, ``id``, ``field``, ``join_model``, ``output_schema`` and (for POST/PATCH)
    ``deserialized_data``. Return a dict to update the call-time kwargs (e.g., mutate
    ``deserialized_data``).

- after_model_op(context: dict, output: Any) -> Any | None
    Runs after a CRUD action. Return a value to replace the output before serialisation.

- spec_build_started(spec: apispec.APISpec) -> None
    Called when building the OpenAPI specification.

- spec_build_completed(spec_dict: dict) -> dict | None
    Called after the spec is converted to a dictionary. Return a dict to replace it.

Notes
-----

- Plugins are additive: multiple plugins can be installed; they are called in order.
- Returning ``None`` means "no change". Where supported, the first non-``None`` return
  value wins (e.g., response replacement).
- Existing callback config keys (e.g., ``API_SETUP_CALLBACK``) continue to work and
  compose with plugins.

