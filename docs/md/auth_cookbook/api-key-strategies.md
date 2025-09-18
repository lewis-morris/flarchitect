[← Back to Auth Cookbook index](index.md)

# API key strategies
Lookup function (flexible):
```
def lookup_user_by_token(token: str) -> User | None:
    return User.query.filter_by(api_key=token).first()

app.config.update(
    API_AUTHENTICATE_METHOD=["api_key"],
    API_KEY_AUTH_AND_RETURN_METHOD=staticmethod(lookup_user_by_token),
)
```
Hashed field (safer at rest):
```
app.config.update(
    API_AUTHENTICATE_METHOD=["api_key"],
    API_USER_MODEL=User,
    API_CREDENTIAL_HASH_FIELD="api_key_hash",
    API_CREDENTIAL_CHECK_METHOD="check_api_key",
)
```
Clients send `Authorization: Api-Key <token>`.

