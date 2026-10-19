[← Back to Extend the generated API index](index.md)

# Managed routes: one decorator
```
@architect.route("/health", methods=["GET"], auth=False)
def health():
    return {"healthy": True}

@architect.route("/echo", methods=["POST"], input_schema=ApprovalInput)
def echo(deserialized_data):
    return deserialized_data
```
Paths are full Flask paths: `API_PREFIX` is not added to `route`. Use Flask
path variables as usual. `endpoint` sets an explicit Flask endpoint name;
remaining options go to `schema_constructor`. Without an output schema,
dictionaries are wrapped in the normal response envelope. These routes receive
the same wrapper validation, authentication, rate limiting and documentation
as manual routes, but do not automatically load records or manage transactions.
Conflicting paths/methods raise a setup error rather than silently replacing a
route. To replace generated CRUD, use `override`. Existing Flask blueprints
and `@app.route` plus `@architect.schema_constructor` remain available.
