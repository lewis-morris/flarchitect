[← Back to WebSockets index](index.md)

# Client Example
Vanilla browser client subscribing to all events and logging them:
```
<script>
  const ws = new WebSocket("ws://localhost:5000/ws");
  ws.onmessage = (evt) => {
    const data = JSON.parse(evt.data);
    console.log(`[${data.model}] ${data.method}`, data.payload);
  };
  ws.onopen = () => console.log("WS connected");
  ws.onclose = () => console.log("WS closed");
</script>
```
Python client using `websockets`:
```
import asyncio, json, websockets

async def main():
    async with websockets.connect("ws://localhost:5000/ws?topic=author") as ws:
        async for message in ws:
            event = json.loads(message)
            print("author event:", event)

asyncio.run(main())
```

