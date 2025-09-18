[← Back to Authentication index](index.md)

# Config-driven roles
You can assign roles to endpoints without decorating functions by setting a
single map in configuration or on a model's `Meta`. This is the most
maintainable way to protect all generated CRUD routes consistently.
Use `API_ROLE_MAP` with method names as keys. Values may be a list of roles
that must all be present, a string for a single role, or a dictionary with an
`any_of` flag for “any of these roles” semantics.
Global example (applies to all models):
```
app.config.update(
    API_AUTHENTICATE_METHOD=["jwt"],  # ensure authentication is enabled
    API_ROLE_MAP={
        "GET": ["viewer"],                  # both list & string forms are accepted
        "POST": {"roles": ["editor", "admin"], "any_of": True},
        "PATCH": ["editor", "admin"],       # require all listed roles
        "DELETE": ["admin"],
        "ALL": True,                         # optional: means "auth-only" for any unspecified methods
    },
)
```
Model-specific example (overrides global for this model only):
```
class Book(Base):
    __tablename__ = "books"

    class Meta:
        api_role_map = {
            "GET_MANY": ["viewer"],
            "GET_ONE": ["viewer"],
            "POST": ["editor"],
            "PATCH": {"roles": ["editor", "admin"], "any_of": True},
            "DELETE": ["admin"],
        }
```

## Recognised keys
- `GET`, `POST`, `PATCH`, `DELETE`: Protects the corresponding CRUD endpoints.
- `GET_MANY` / `GET_ONE`: Optional split for collection vs single-item GET.
- `RELATION_GET`: Protects relation endpoints like `/parents/{id}/children`.
- `ALL` or `*`: Fallback applied when a method key is not present.

## Fallbacks
If you prefer very simple policies, instead of `API_ROLE_MAP` you can set one
of the following (globally or on a model's `Meta`):
- `API_ROLES_REQUIRED`: list of roles, all must be present.
- `API_ROLES_ACCEPTED`: list of roles where any grants access.
These apply to all endpoints for that model and are overridden by
`API_ROLE_MAP` when both are present.

