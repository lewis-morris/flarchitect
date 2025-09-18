[← Back to API Documentation index](index.md)

# Error responses in the spec
flarchitect includes common error responses in each operation based on your
configuration and the route’s context:
- 401/403: shown when `API_AUTHENTICATE` is enabled, or when a route explicitly declares them (e.g., `/auth/refresh`).
- 429: shown when a rate limit is configured via `API_RATE_LIMIT`; standard rate-limit headers are documented.
- 400: shown when a request body is validated (input schema present) or for list endpoints with filtering/pagination features enabled. When API_ALLOW_JOIN <configuration.html#ALLOW_JOIN> is enabled, invalid join tokens (unknown relationships) also produce `400` with a message like `Invalid join model: <token>`.
- 422: shown on `POST`/`PUT`/`PATCH` for models, reflecting integrity/type errors.
- 404: shown for single-resource lookups and relationship endpoints.
- 409: shown for `DELETE` (conflicts with related data or cascade rules).
- 500: included by default unless you override the error list.
You can override the default set for a specific route by supplying
`error_responses=[...]` to `@architect.schema_constructor`.

