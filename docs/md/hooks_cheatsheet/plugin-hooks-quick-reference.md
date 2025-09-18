[← Back to Hooks & Plugins Cheatsheet index](index.md)

# Plugin hooks quick reference
- request_started(request) -> None
    - First hook at request start.
- before_authenticate(context: dict) -> dict | None
    - Context: model, method, output_schema?, input_schema?.
- after_authenticate(context: dict, success: bool, user: Any | None) -> None
- before_model_op(context: dict) -> dict | None
    - Context: model, method, many, id, field, join_model, relation_name,
    > output_schema, deserialized_data.
- after_model_op(context: dict, output: Any) -> Any | None
- spec_build_started(spec) -> None
- spec_build_completed(spec_dict: dict) -> dict | None
- request_finished(request, response) -> flask.Response | None
    - Last hook, may replace the response.

