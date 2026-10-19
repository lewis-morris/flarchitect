[← Back to Extend the generated API index](index.md)

# Transaction ownership
For write actions and mutation overrides, flarchitect flushes changes before
serialisation and commits only after the response is successfully constructed.
Handler exceptions, validation/serialisation errors and unsuccessful responses
roll back the session. Handlers must not commit or close the session themselves.
Use `context.session.flush()` when you need an ID earlier.
The transaction covers the resolved SQLAlchemy session only. External services,
email, and other databases cannot be rolled back by flarchitect. Keep durable
external work behind an outbox or your application's own delivery mechanism.
GET actions are read-only: their session is rolled back after the response.
Ordinary generated CRUD keeps its existing commit timing.
