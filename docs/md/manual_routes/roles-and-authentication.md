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

