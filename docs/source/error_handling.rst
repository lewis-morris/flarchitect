Error Handling
=========================================

flarchitect standardises error reporting through a small set of helpers. These
utilities ensure your API returns consistent payloads regardless of where an
exception originates.

CustomHTTPException
-------------------

``CustomHTTPException`` is a lightweight wrapper around an HTTP status code and
optional reason. Raise it in your views when you need to abort a request with a
specific status::

   from flarchitect.exceptions import CustomHTTPException

   @app.get("/widgets/<int:id>")
   def get_widget(id: int):
       widget = Widget.query.get(id)
       if widget is None:
           raise CustomHTTPException(404, "Widget not found")
       return widget

The exception exposes a ``to_dict`` method which yields a structured payload
containing the ``status_code``, ``status_text`` and ``reason`` fields.

handle_http_exception
---------------------

Register ``handle_http_exception`` as the Flask error handler for
``CustomHTTPException`` to automatically serialise the exception into a
``create_response`` payload::

   from flarchitect.exceptions import CustomHTTPException, handle_http_exception

   app.register_error_handler(CustomHTTPException, handle_http_exception)

A ``404`` from the example above produces the following JSON response:

.. code-block:: json

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

Using ``_handle_exception``
---------------------------

For ad-hoc exception handling you can call ``_handle_exception`` directly. It
accepts an error string, HTTP status code and optional reason, returning the
same structured response used throughout the library::

   from flarchitect.exceptions import _handle_exception

   @app.get("/divide")
   def divide() -> Response:
       try:
           result = expensive_division()
       except ZeroDivisionError as exc:
           return _handle_exception("Bad Request", 400, str(exc))
       return {"value": result}

This helper is useful when catching non-Flask exceptions but still wanting a
uniform error format.

Common status codes
-------------------

flarchitect normalises a consistent set of HTTP statuses across endpoints:

- 400 Bad Request: validation errors (Marshmallow deserialisation), invalid query parameters, malformed inputs (e.g., missing refresh token), and SQL formatting issues.
- 401 Unauthorized: missing/invalid Authorization header, invalid JWT (bad signature/claims), unauthenticated access to protected routes.
- 403 Forbidden: insufficient roles or permissions, invalid/revoked/expired-in-store refresh tokens.
- 404 Not Found: resource lookup by id or relationship yields no results; user not found during token refresh.
- 409 Conflict: delete operations blocked by related records or cascade rules.
- 422 Unprocessable Entity: database integrity or data type errors on create/update (e.g., uniqueness violations).
- 429 Too Many Requests: rate limit exceeded when ``API_RATE_LIMIT`` is configured (headers include standard rate-limit fields).
- 405 Method Not Allowed: Flask-level response when an endpoint does not support the HTTP method; serialised by the default error handler for API routes.
- 500 Internal Server Error: uncaught exceptions or misconfiguration (e.g., missing JWT keys, soft delete misconfiguration).
