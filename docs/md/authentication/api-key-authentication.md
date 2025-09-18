[← Back to Authentication index](index.md)

# API key authentication
API key auth associates a user with a single token. Clients send the token in
each request via an `Authorization` header using the `Api-Key` scheme. The
framework passes the token to a function you provide (or validates a stored
hash) and uses the returned user for the request.
If you store hashed tokens on the model, set API_CREDENTIAL_HASH_FIELD <configuration.html#CREDENTIAL_HASH_FIELD> to the attribute holding the hash so flarchitect can validate keys.
Attach a function that accepts an API key and returns a user. The function can
also call `set_current_user`:
```
def lookup_user_by_token(token: str) -> User | None:
    user = User.query.filter_by(api_key=token).first()
    if user:
        set_current_user(user)
    return user

class Config(BaseConfig):
    API_AUTHENTICATE_METHOD = ["api_key"]
    API_KEY_AUTH_AND_RETURN_METHOD = staticmethod(lookup_user_by_token)
```
When this method is enabled flarchitect exposes a companion login route. POST
an `Api-Key` `Authorization` header to `/auth/login` to validate the key
and retrieve basic user details:
```
curl -X POST -H "Authorization: Api-Key <token>" http://localhost:5000/auth/login
```
Clients include the API key with each request using:
```
curl -H "Authorization: Api-Key <token>" http://localhost:5000/api/books
```
See `demo/authentication/api_key_auth.py` for more detail.

