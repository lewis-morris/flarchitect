[← Back to Extend the generated API index](index.md)

# Overrides: replace one operation
```
@architect.override(Order, "create")
def create_order(data, context):
    return Order(name=data["name"].strip().upper())
```
Only the generated create implementation changes. Input validation, output
schema, authentication, roles, rate limits and OpenAPI stay in place. An override
applies to the model's canonical and alternate CRUD paths, not relationship
operations. Registering a second override for the same operation, or an override
for an operation that has no generated route, fails during setup.
Supported contracts:
- `create(data, context)`: receives validated input and returns a model
    instance. The framework adds it to the session and flushes its generated ID.
- `update(record, context)`: receives the scoped, authorised record; read the
    validated patch from `context.data` and apply your changes explicitly.
    Return a model instance.
- `delete(record, context)`: receives the scoped, authorised record. Perform
    the deletion with `context.session.delete(record)` or implement your own
    soft delete. Return `None`; the framework emits the standard success response.
- `retrieve(record, context)`: receives the visible record and returns the
    value to serialise with the existing output schema.
- `list(query, context)`: receives the generated query, after normal filters
    and query hooks, and must return a SQLAlchemy Query. Sorting, soft-delete
    filtering, counts and pagination still run afterwards. Policy scope is
    reapplied so a replacement query cannot drop it. Keep the query's model shape;
    use a managed route for reports with unrelated rows or aggregates.
Mutation overrides replace the persistence implementation, including legacy
add/update/remove callbacks. The new `before_create` and `before_update`
hooks still run on the returned model. A delete override owns its own deletion
behaviour; use the built-in deletion and `before_delete` when you only need a
small adjustment. Generated setup/return callbacks and operation plugins remain
around the replacement operation.
