# CORS Demo

This example enables Cross-Origin Resource Sharing using `API_ENABLE_CORS`.
Requests to `/ping` return an `Access-Control-Allow-Origin` header, allowing
clients from any origin to call the API.

## Run

```bash
python demo/cors/app.py
```

Verify the header:

```bash
curl -i -H "Origin: http://example.com" http://127.0.0.1:5000/ping
```

The response includes `Access-Control-Allow-Origin: *` confirming CORS is
active.
