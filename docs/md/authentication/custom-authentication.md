[← Back to Authentication index](index.md)

# Custom authentication
For complete control supply your own callable. This method lets you support any
authentication strategy you like: session cookies, HMAC signatures or
third-party OAuth flows. Your callable should return `True` on success and may
call `set_current_user` to attach the authenticated user to the request.
```
def custom_auth() -> bool:
    token = request.headers.get("X-Token", "")
    user = User.query.filter_by(api_key=token).first()
    if user:
        set_current_user(user)
        return True
    return False

class Config(BaseConfig):
    API_AUTHENTICATE_METHOD = ["custom"]
    API_CUSTOM_AUTH = staticmethod(custom_auth)
```
Clients can then call your API with whatever headers your function expects:
```
curl -H "X-Token: <token>" http://localhost:5000/api/books
```
See `demo/authentication/custom_auth.py` for this approach in context.

