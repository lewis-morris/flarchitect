[← Back to Extensions index](index.md)

# Callback signatures

## Setup, Global setup and filter
Setup‑style callbacks receive `model` and a set of keyword arguments
describing the operation. They must return a dict (possibly empty) which will
be merged into the route's processing context.
Common `**kwargs` keys (availability depends on the route):
- `id`: int | str | None – primary key value for single‑item routes
- `field`: str | None – alternative lookup field name when configured
- `join_model`: type | None – relationship model for relation routes
- `output_schema`: marshmallow.Schema | None – response schema
- `relation_name`: str | None – relation attribute name (relation routes)
- `deserialized_data`: dict | None – request body deserialised by the input schema
- `many`: bool – whether the route returns a collection
- `method`: str – HTTP method (e.g., "GET")
Return value: `dict[str, Any]` to merge back into kwargs.
Examples:
.. code-block:: python
> **def my_setup_callback(model, **kwargs):**
>
> # modify kwargs as needed
> return kwargs
>
> **def my_filter_callback(query, model, params):**
> return query.filter(model.id > 0)

## Add, update and remove
These callbacks receive the SQLAlchemy object instance and must return it:
```
def my_add_callback(obj, model):
    obj.created_by = "system"
    return obj
```

## Return
Return callbacks receive `model`, `output` and `**kwargs` (same keys as
Setup). They must return a dict containing the `output` key. The callback can
wrap or transform the output. Typical shapes for `output` are:
- GET many: `{"query": list[Model], "limit": int, "page": int, "total_count": int}`
- GET one: `{"query": Model}`
- POST/PATCH: the created/updated model instance or a result dict
- DELETE: `(None, 200)` when soft‑delete/OK
```
def my_return_callback(model, output, **kwargs):
    return {"output": output}
```

## Dump
Dump callbacks accept `data` and `**kwargs` and must return the data:
```
def my_dump_callback(data, **kwargs):
    data["name"] = data["name"].upper()
    return data
```

## Final
Final callbacks receive the response dictionary before it is serialised:
```
def my_final_callback(data):
    data["processed"] = True
    return data
```

## Error
Error callbacks receive the error message, status code and a value payload
constructed by the response wrapper. Use this to send notifications or add
structured logs.
```
def my_error_callback(error, status_code, value):
    log_exception(error)
```

