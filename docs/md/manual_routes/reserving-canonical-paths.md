[← Back to Manual Routes index](index.md)

# Reserving canonical paths
By default *flarchitect* registers RESTful collection/detail routes for every
model under the canonical prefix (for example `/api/orders` and
`/api/orders/<id>`). Projects that need bespoke logic for those URLs can turn
the automatic routes off while still relying on auto-generated schemas,
relations and alternate endpoints.
- Disable the feature globally with
    `API_REGISTER_CANONICAL_ROUTES = False`.
- Override per model via `Meta.register_canonical_routes = False`.
- Supply alternate auto-generated endpoints with `Meta.endpoint` (string or
    list) so CRUD handlers remain available under a different prefix.
Example:
```
class Config:
    API_REGISTER_CANONICAL_ROUTES = False  # keep /api/v1/orders for bespoke handlers

class Order(db.Model):
    __tablename__ = "orders"

    class Meta:
        tag = "Order"
        register_canonical_routes = False
        endpoint = "orders/records"  # auto CRUD lives here instead

@app.get("/api/v1/orders")
def bespoke_orders():
    """Your custom collection handler."""
    ...
```
The default remains `True` so existing projects keep their canonical routes
until they opt out. Relation endpoints and discovery continue to work because
the underlying services are still created.
