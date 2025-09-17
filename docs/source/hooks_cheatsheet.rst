Hooks & Plugins Cheatsheet
=========================================

Quick reference for callbacks and plugin hooks: when they run, what they
receive, and what they should return.

Lifecycle at a glance
---------------------

.. code-block:: text

   Request -> [Plugin: request_started]
           -> [Auth: before_authenticate] -> (authenticate) -> [after_authenticate]
           -> [Route (schema_constructor)]:
                -> Plugin: before_model_op(context)
                -> API_GLOBAL_SETUP_CALLBACK(model, **kwargs) -> dict
                -> API_SETUP_CALLBACK(model, **kwargs) -> dict
                -> CRUD Action
                   -> API_FILTER_CALLBACK(query, model, params) -> query
                   -> API_ADD_CALLBACK(obj, model) -> obj (POST)
                   -> API_UPDATE_CALLBACK(obj, model) -> obj (PATCH)
                   -> API_REMOVE_CALLBACK(obj, model) -> obj (DELETE)
                -> API_RETURN_CALLBACK(model, output, **kwargs) -> {"output": ...}
                -> Plugin: after_model_op(context, output)
           -> Marshmallow dump -> API_DUMP_CALLBACK(data, **kwargs) -> data
           -> create_response(...) JSON envelope -> API_FINAL_CALLBACK(dict) -> dict
           -> [Errors trigger API_ERROR_CALLBACK(error, status_code, value)]
           -> [Plugin: request_finished(request, response)] -> Response

Callback quick reference
------------------------

- API_GLOBAL_SETUP_CALLBACK(model, **kwargs) -> dict
  - When: Before any model-specific processing for a route.
  - kwargs keys: id, field, join_model, output_schema, relation_name,
    deserialized_data, many, method.
  - Return: dict to merge back into kwargs.

- API_SETUP_CALLBACK(model, **kwargs) -> dict
  - When: Before database operations on a route.
  - kwargs/return: same as GLOBAL_SETUP_CALLBACK.

- API_FILTER_CALLBACK(query, model, params) -> sqlalchemy.orm.Query
  - When: While building a GET query, before paging/sorting.
  - Params: request args dict.

- API_ADD_CALLBACK(obj, model) -> obj
  - When: Right before commit on POST.

- API_UPDATE_CALLBACK(obj, model) -> obj
  - When: Right before commit on PATCH.

- API_REMOVE_CALLBACK(obj, model) -> obj
  - When: Before DELETE (or soft delete) is applied.

- API_RETURN_CALLBACK(model, output, **kwargs) -> {"output": Any}
  - When: After the CRUD action but before serialisation/response.
  - Output shapes: {"query": list | item, ...} for GET, model instance or dict for POST/PATCH, (None, 200) for DELETE.

- API_DUMP_CALLBACK(data, **kwargs) -> dict
  - When: After Marshmallow serialisation.

- API_FINAL_CALLBACK(data: dict) -> dict
  - When: Immediately before the JSON response is emitted.

- API_ERROR_CALLBACK(error: str, status_code: int, value: Any) -> None
  - When: On any error handled by the response wrapper.

Plugin hooks quick reference
---------------------------

- request_started(request) -> None
  - First hook at request start.

- before_authenticate(context: dict) -> dict | None
  - Context: model, method, output_schema?, input_schema?.

- after_authenticate(context: dict, success: bool, user: Any | None) -> None

- before_model_op(context: dict) -> dict | None
  - Context: model, method, many, id, field, join_model, relation_name,
    output_schema, deserialized_data.

- after_model_op(context: dict, output: Any) -> Any | None

- spec_build_started(spec) -> None
- spec_build_completed(spec_dict: dict) -> dict | None

- request_finished(request, response) -> flask.Response | None
  - Last hook, may replace the response.

