[← Back to Extend the generated API index](index.md)

# Hooks: keep the generated implementation
All hooks take `(value, context)`. Return a replacement value, or return
`None` to keep the current value after modifying it. Multiple hooks run in
registration order, after the corresponding legacy callback.
```
@architect.hook(Order, "query")
def open_orders(query, context):
    return query.filter(Order.status == "open")

@architect.hook(Order, "before_update")
def check_order(order, context):
    if order.quantity < 1:
        abort(422, "Quantity must be at least one")
    return order
```
Available events:
- `query`: receives the collection Query before sorting, counting and
    pagination. Access-policy scope is reapplied afterwards. It does not filter
    detail reads or mutations; use an access policy for restrictions that must
    apply everywhere.
- `before_create`: receives the constructed record before it is saved.
- `before_update`: receives the record with validated changes applied, before
    saving.
- `before_delete`: receives the record before the built-in deletion.
- `after_operation`: receives the record or list of records before
    serialisation; pagination metadata stays managed by the framework. Creates
    and updates supply the record, and actions supply their handler's return value.
    Deletion supplies the existing `(None, 200)` success tuple.
`after_operation` is for response adjustments, not validation or external
side effects: ordinary generated writes have already committed at that point.
Use a before hook for validation. Extra response fields must also be declared
in your output schema.
