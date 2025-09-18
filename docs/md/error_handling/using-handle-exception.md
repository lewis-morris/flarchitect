[← Back to Error Handling index](index.md)

# Using `_handle_exception`
For ad-hoc exception handling you can call `_handle_exception` directly. It
accepts an error string, HTTP status code and optional reason, returning the
same structured response used throughout the library:
```
from flarchitect.exceptions import _handle_exception

@app.get("/divide")
def divide() -> Response:
    try:
        result = expensive_division()
    except ZeroDivisionError as exc:
        return _handle_exception("Bad Request", 400, str(exc))
    return {"value": result}
```
This helper is useful when catching non-Flask exceptions but still wanting a
uniform error format.

