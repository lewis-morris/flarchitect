[← Back to Manual Routes index](index.md)

# Roles and authentication
If your application uses role‑based access control, supply `roles` to require
users to have specific roles on this route. By default, when authentication is
enabled globally, roles are enforced automatically for decorated routes.
```
@app.get("/admin/stats")
@architect.schema_constructor(output_schema=HelloOut, roles=["admin"])  # require the "admin" role
def admin_stats():
    return {"message": "ok"}
```
To allow access when the user has any of multiple roles, either set
`roles_any_of=True` or pass a dict with `{"roles": [...], "any_of": True}`:
```
@app.get("/content/edit")
@architect.schema_constructor(output_schema=HelloOut, roles=["editor", "admin"], roles_any_of=True)
def edit_content():
    return {"message": "ok"}


# equivalent
@app.get("/content/edit-alt")
@architect.schema_constructor(output_schema=HelloOut, roles={"roles": ["editor", "admin"], "any_of": True})
def edit_content_alt():
    return {"message": "ok"}
```
To opt out of authentication for a specific manual route, set `auth=False`:
```
@app.get("/public/ping")
@architect.schema_constructor(output_schema=HelloOut, auth=False)
def public_ping():
    return {"message": "pong"}
```
Alternatively, configure `API_AUTH_REQUIREMENTS` to opt HTTP verbs or route
flavours in/out of authentication at the config level. Manual routes decorated
with `schema_constructor` honour the map—use it to make every `GET` route
public, for instance, without adding `auth=False` repeatedly. Apply
`API_ACCESS_POLICY` when you need row-level checks so both generated and
manual endpoints share the same access logic.
When working with cookie-based credentials, combine `API_AUTH_TOKEN_PROVIDERS`
(for example `['cookie', 'header']`) with the
`load_user_from_cookie` helper to populate `current_user` outside the
standard auth flow. Use flarchitect.utils.cookie_settings to retrieve
project-aligned cookie keyword arguments (merged from `API_COOKIE_DEFAULTS`
and `SESSION_COOKIE_*`) whenever you issue or clear cookies.

