[← Back to Authentication index](index.md)

# Role-based access
Use the `require_roles` decorator to restrict access based on user roles. The
decorator reads `current_user.roles` which is populated by the active
authentication method.
```
from flarchitect.authentication import require_roles

@app.get("/admin")
@require_roles("admin")
def admin_dashboard():
    return {"status": "ok"}
```
Pass multiple roles to require all of them. To allow access when a user has
*any* of the listed roles, set `any_of=True`:
```
@require_roles("admin", "editor", any_of=True)
def update_post():
    ...
```

## Defining roles
Roles can be attached to the user model or embedded in authentication tokens so
`require_roles` can evaluate permissions.

### JWT
1. Persist a `roles` attribute on the user model, e.g. `User.roles = ["admin"]`.
2. `require_roles` reads roles from `current_user` after the token is
    validated and the user is loaded.

### API keys
1. Store roles on the user model.
2. In the lookup function, return a user object with those roles:
    ```
    def lookup_user_by_token(token: str) -> User | None:
        user = User.query.filter_by(api_key=token).first()
        if user:
            set_current_user(user)
        return user
    ```
3. `require_roles` pulls roles from `current_user`.

### Custom authentication
1. Resolve the user from your custom credentials.
2. Call `set_current_user` with an object exposing `roles`.
3. `require_roles` authorises the request using those roles.

### Common roles
| Role | Responsibility |
| --- | --- |
| `admin` | Full access to manage resources and users. |
| `editor` | Create and modify resources but cannot manage users. |
| `viewer` | Read-only access to resources. |
If the authenticated user lacks any of the required roles—or if no user is
authenticated—a `403` response is raised.

