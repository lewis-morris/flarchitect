[← Back to Plugins index](index.md)

# Hook reference
Stable hook signatures (kwargs may grow over time):
- **request_started(request: flask.Request) -> None**
    Called at the beginning of each request.
- **request_finished(request: flask.Request, response: flask.Response) -> flask.Response | None**
    Called after a response is created. Return a replacement Response to override.
- **before_authenticate(context: dict) -> dict | None**
    Runs prior to authentication (for non-schema routes and schema routes alike).
    May return a dict of updates to merge into the context.
- **after_authenticate(context: dict, success: bool, user: Any | None) -> None**
    Runs after authentication attempt.
- **before_model_op(context: dict) -> dict | None**
    Runs before a CRUD action. Context includes keys such as `model`, `method`,
    `many`, `id`, `field`, `join_model`, `output_schema` and (for POST/PATCH)
    `deserialized_data`. Return a dict to update the call-time kwargs (e.g., mutate
    `deserialized_data`).
- **after_model_op(context: dict, output: Any) -> Any | None**
    Runs after a CRUD action. Return a value to replace the output before serialisation.
- **spec_build_started(spec: apispec.APISpec) -> None**
    Called when building the OpenAPI specification.
- **spec_build_completed(spec_dict: dict) -> dict | None**
    Called after the spec is converted to a dictionary. Return a dict to replace it.

