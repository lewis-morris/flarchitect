[← Back to SQLAlchemy Models index](index.md)

# Dump types
`flarchitect` can serialise model responses in different formats, controlled
by API_SERIALIZATION_TYPE <configuration.html#SERIALIZATION_TYPE> or `Meta.serialization_type`. Supported dump
types are:
- `url` (default) – represent related objects only by their URL links.
- `json` – embed related objects as JSON objects.
- `dynamic` – choose between `url` and `json` using the `dump` query
    parameter.
- `hybrid` – include both URL links and embedded JSON for related objects.
Example:
```
class Config:
    API_SERIALIZATION_TYPE = "json"
```
Clients can override `dynamic` dumps per request with
`?dump=url` or `?dump=json`.

