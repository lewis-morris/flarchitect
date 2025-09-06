WebSockets
=========================================

Overview
--------

flarchitect ships with a lightweight, optional WebSocket integration intended
for real‑time UI updates, dashboards, or background workers that react to API
changes. When enabled, every CRUD route publishes an event after completing
its work. Clients can subscribe over a single WebSocket endpoint to receive
JSON messages per model or for all models.

Key points:

- Uses an in‑memory pub/sub bus suitable for single‑process deployments.
- Exposes one WebSocket route (default: ``/ws``) via ``flask_sock`` if
  installed; otherwise it is a no‑op.
- Broadcasts on topics per model name (lowercase), plus a global ``all``
  topic.

Enable The Endpoint
-------------------

1. Install the optional dependency:

   pip install flask-sock

2. Enable WebSockets in your Flask config and (optionally) set the path:

.. code-block:: python

    class Config:
        API_ENABLE_WEBSOCKETS = True
        API_WEBSOCKET_PATH = "/ws"  # optional, defaults to "/ws"

3. Initialise flarchitect as usual. If ``flask_sock`` is present, the
   ``/ws`` route is registered automatically:

.. code-block:: python

    app = Flask(__name__)
    architect = Architect(app)
    # no extra steps required

Subscription Model
------------------

Subscribe to a topic by connecting to the endpoint with an optional ``topic``
query parameter. Without a topic, the server subscribes you to ``all``.

Examples:

- All models: ``ws://localhost:5000/ws``
- Specific model: ``ws://localhost:5000/ws?topic=author``

Message Format
--------------

Each message is a single JSON object sent as a text frame:

.. code-block:: json

    {
      "ts": 1712345678901,
      "model": "author",
      "method": "POST",
      "id": 42,
      "many": false,
      "payload": { "id": 42, "name": "Ada" }
    }

- ``model``: lower‑case model name.
- ``method``: HTTP method that triggered the event.
- ``id``: primary key for single‑record calls if available.
- ``many``: whether the response includes a list.
- ``payload``: the same data returned by the REST endpoint after all
  callbacks and serialisation.

Client Example
--------------

Vanilla browser client subscribing to all events and logging them:

.. code-block:: html

    <script>
      const ws = new WebSocket("ws://localhost:5000/ws");
      ws.onmessage = (evt) => {
        const data = JSON.parse(evt.data);
        console.log(`[${data.model}] ${data.method}`, data.payload);
      };
      ws.onopen = () => console.log("WS connected");
      ws.onclose = () => console.log("WS closed");
    </script>

Python client using ``websockets``:

.. code-block:: python

    import asyncio, json, websockets

    async def main():
        async with websockets.connect("ws://localhost:5000/ws?topic=author") as ws:
            async for message in ws:
                event = json.loads(message)
                print("author event:", event)

    asyncio.run(main())

How It Works
------------

- A tiny in‑memory event bus (``flarchitect.core.websockets``) tracks topic
  subscribers and broadcasts events.
- Route handlers publish a message after executing your callbacks, inside the
  normal request cycle. If broadcasting fails, it never breaks the response.
- When ``API_ENABLE_WEBSOCKETS`` is set and ``flask_sock`` is installed, a
  WebSocket route is registered with the Flask app. It forwards pub/sub
  messages as JSON text frames.

Notes & Limitations
-------------------

- The default bus is process‑local and not durable; it is ideal for
  development or single‑process servers. For multi‑worker production setups
  you should replace the event bus with a real broker (Redis, NATS, etc.) and
  adapt publish/subscribe accordingly.
- No authentication is enforced on the WebSocket endpoint. If required,
  protect the route via a proxy (e.g. nginx) or fork the helper and add JWT
  checks.

