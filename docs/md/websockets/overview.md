[← Back to WebSockets index](index.md)

# Overview
flarchitect ships with a lightweight, optional WebSocket integration intended
for real‑time UI updates, dashboards, or background workers that react to API
changes. When enabled, every CRUD route publishes an event after completing
its work. Clients can subscribe over a single WebSocket endpoint to receive
JSON messages per model or for all models.
Key points:
- Uses an in‑memory pub/sub bus suitable for single‑process deployments.
- Exposes one WebSocket route (default: `/ws`) via `flask_sock` if
    installed; otherwise it is a no‑op.
- Broadcasts on topics per model name (lowercase), plus a global `all`
    topic.

