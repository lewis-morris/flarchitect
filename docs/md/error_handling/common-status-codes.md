[← Back to Error Handling index](index.md)

# Common status codes
flarchitect normalises a consistent set of HTTP statuses across endpoints:
- 400 Bad Request: validation errors (Marshmallow deserialisation), invalid query parameters, malformed inputs (e.g., missing refresh token), and SQL formatting issues.
- 401 Unauthorized: missing/invalid Authorization header, invalid JWT (bad signature/claims), unauthenticated access to protected routes.
- 403 Forbidden: insufficient roles or permissions, invalid/revoked/expired-in-store refresh tokens.
- 404 Not Found: resource lookup by id or relationship yields no results; user not found during token refresh.
- 409 Conflict: delete operations blocked by related records or cascade rules.
- 422 Unprocessable Entity: database integrity or data type errors on create/update (e.g., uniqueness violations).
- 429 Too Many Requests: rate limit exceeded when `API_RATE_LIMIT` is configured (headers include standard rate-limit fields).
- 405 Method Not Allowed: Flask-level response when an endpoint does not support the HTTP method; serialised by the default error handler for API routes.
- 500 Internal Server Error: uncaught exceptions or misconfiguration (e.g., missing JWT keys, soft delete misconfiguration).

