[← Back to WebSockets index](index.md)

# Message Format
Each message is a single JSON object sent as a text frame:
```
{
  "ts": 1712345678901,
  "model": "author",
  "method": "POST",
  "id": 42,
  "many": false,
  "payload": { "id": 42, "name": "Ada" }
}
```
- `model`: lower‑case model name.
- `method`: HTTP method that triggered the event.
- `id`: primary key for single‑record calls if available.
- `many`: whether the response includes a list.
- `payload`: the same data returned by the REST endpoint after all
    callbacks and serialisation.

