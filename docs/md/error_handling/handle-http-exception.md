[← Back to Error Handling index](index.md)

# handle_http_exception
Register `handle_http_exception` as the Flask error handler for
`CustomHTTPException` to automatically serialise the exception into a
`create_response` payload:
```
from flarchitect.exceptions import CustomHTTPException, handle_http_exception

app.register_error_handler(CustomHTTPException, handle_http_exception)
```
A `404` from the example above produces the following JSON response:
```
{
  "api_version": "0.1.0",
  "datetime": "2024-01-01T00:00:00+00:00",
  "status_code": 404,
  "errors": {"error": "Not Found", "reason": "Widget not found"},
  "response_ms": 5.0,
  "total_count": 1,
  "next_url": null,
  "previous_url": null,
  "value": null
}
```

