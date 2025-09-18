[← Back to WebSockets index](index.md)

# Notes & Limitations
- The default bus is process‑local and not durable; it is ideal for
    development or single‑process servers. For multi‑worker production setups
    you should replace the event bus with a real broker (Redis, NATS, etc.) and
    adapt publish/subscribe accordingly.
- No authentication is enforced on the WebSocket endpoint. If required,
    protect the route via a proxy (e.g. nginx) or fork the helper and add JWT
    checks.

