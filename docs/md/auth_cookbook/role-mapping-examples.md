[← Back to Auth Cookbook index](index.md)

# Role mapping examples
Decorator‑based RBAC:
```
from flarchitect.authentication import require_roles
from flarchitect.core.architect import jwt_authentication

@app.get("/admin")
@jwt_authentication
@require_roles("admin")
def admin_panel():
    ...
```
Config‑driven roles (no decorators):
```
app.config.update(
    API_AUTHENTICATE_METHOD=["jwt"],
    API_ROLE_MAP={
        "GET": ["viewer"],
        "POST": {"roles": ["editor", "admin"], "any_of": True},
        "PATCH": ["editor", "admin"],
        "DELETE": ["admin"],
        # Optional catch‑all to require auth for unspecified methods
        "ALL": True,
    },
)
```
See roles-required and the reference authentication for details.

