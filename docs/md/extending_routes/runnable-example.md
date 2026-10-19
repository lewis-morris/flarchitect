[← Back to Extend the generated API index](index.md)

# Runnable example
See `demo/extensions/app.py` for a complete in-memory application containing
a hook, action, create override and managed route. Run it from the repository:
```
python -m demo.extensions.app
curl -X POST http://127.0.0.1:5000/api/orders \
  -H 'Content-Type: application/json' -d '{"name":"new order"}'
curl -X POST http://127.0.0.1:5000/api/orders/1/approve
curl http://127.0.0.1:5000/docs/apispec.json
```
The demonstration disables authentication for local use; configure authentication
and access policies before exposing an application to other users.
