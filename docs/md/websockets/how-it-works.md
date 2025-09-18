[← Back to WebSockets index](index.md)

# How It Works
- A tiny in‑memory event bus (`flarchitect.core.websockets`) tracks topic
    subscribers and broadcasts events.
- Route handlers publish a message after executing your callbacks, inside the
    normal request cycle. If broadcasting fails, it never breaks the response.
- When `API_ENABLE_WEBSOCKETS` is set and `flask_sock` is installed, a
    WebSocket route is registered with the Flask app. It forwards pub/sub
    messages as JSON text frames.

