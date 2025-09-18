# Extensions

Callbacks let you hook into the request lifecycle to run custom logic around
database operations and responses. They can be declared globally in the Flask
configuration or on individual SQLAlchemy models.
> **Note**
> With `AUTO_NAME_ENDPOINTS` enabled (the default), flarchitect generates a
> summary for each endpoint based on its schema and HTTP method. Disable this
> flag if your callbacks provide custom summaries to prevent them from being
> overwritten.

## Sections

- [Request lifecycle and hook order](request-lifecycle-and-hook-order.md)
- [Callback types](callback-types.md)
- [Configuration](configuration.md)
- [Callback signatures](callback-signatures.md)
- [Plugin hooks](plugin-hooks.md)
- [Extending query parameters](extending-query-parameters.md)
- [Acceptable types](acceptable-types.md)
- [Acceptable formats](acceptable-formats.md)
