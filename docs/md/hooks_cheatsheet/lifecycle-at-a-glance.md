[← Back to Hooks & Plugins Cheatsheet index](index.md)

# Lifecycle at a glance
```
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
```

