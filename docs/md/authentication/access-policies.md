[← Back to Authentication index](index.md)

# Access policies
Attach `API_ACCESS_POLICY` to enforce row-level permissions. The value may be
an instance, class, or mapping exposing any subset of these optional hooks:
- `scope_query(query, *, action, user, request, model, many, relation_name)` –
    return a restricted SQLAlchemy query for GET operations.
- `can_read(obj, *, action, user, request, model, many, relation_name)` –
    control access to a single object after lookup.
- `can_create(data, *, action, user, request, model)` – guard POST payloads.
- `can_update(obj, data, *, action, user, request, model)` – guard PATCH payloads.
- `can_delete(obj, *, action, user, request, model)` – guard DELETE requests.
Missing hooks default to allow-all behaviour. Returning any falsy value raises a
`403` with a generic “Forbidden” response.
```
class OwnerPolicy:
    def scope_query(self, query, *, user, model, **_):
        if user is None:
            return query.filter(False)
        return query.filter(model.owner_id == user.id)

    def can_create(self, data, *, user, **_):
        return user is not None and data.get("owner_id") == user.id

    def can_update(self, obj, data, *, user, **_):
        return user is not None and getattr(obj, "owner_id", None) == user.id

    def can_delete(self, obj, *, user, **_):
        return user is not None and getattr(obj, "owner_id", None) == user.id

app.config.update(
    API_AUTHENTICATE_METHOD=["custom"],
    API_CUSTOM_AUTH=my_custom_auth,
    API_ACCESS_POLICY=OwnerPolicy,
)
```

