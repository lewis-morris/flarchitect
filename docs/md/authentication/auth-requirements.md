[← Back to Authentication index](index.md)

# Auth requirements
Set `API_AUTH_REQUIREMENTS` to enable or disable authentication per HTTP
method or route flavour while keeping a global strategy configured. Keys accept
any HTTP verb, `GET_ONE`, `GET_MANY`, `RELATION_GET_ONE`,
`RELATION_GET_MANY`, `RELATION_GET`, `RELATION_<METHOD>`, `ALL` or
`*`. Values accept booleans (and compatible strings). Missing keys fall back
to the default behaviour where authentication runs whenever
`API_AUTHENTICATE_METHOD` resolves truthy.
```
app.config.update(
    API_AUTHENTICATE_METHOD=["custom"],
    API_AUTH_REQUIREMENTS={
        "GET": False,      # list endpoints are public
        "GET_ONE": True,   # detail endpoints still require auth
        "POST": True,
        "PATCH": True,
        "DELETE": True,
    },
)
```
`schema_constructor` honours the same map for manual routes, while
`auth=False` continues to provide an explicit opt-out for individual views.

