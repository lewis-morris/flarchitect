[← Back to Hooks & Plugins Cheatsheet index](index.md)

# Callback quick reference
- API_GLOBAL_SETUP_CALLBACK(model, **kwargs) -> dict
    - When: Before any model-specific processing for a route.
    - kwargs keys: id, field, join_model, output_schema, relation_name,
    > deserialized_data, many, method.
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

