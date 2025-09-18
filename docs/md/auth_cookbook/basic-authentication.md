[← Back to Auth Cookbook index](index.md)

# Basic authentication
Simple username/password verification against your user model:
```
app.config.update(
    API_AUTHENTICATE_METHOD=["basic"],
    API_USER_MODEL=User,
    API_USER_LOOKUP_FIELD="username",
    API_CREDENTIAL_CHECK_METHOD="check_password",
)
```
Send `Authorization: Basic <base64(username:password)>`. Protect specific
routes with `@architect.schema_constructor(..., auth=True)` or global configs.

