[← Back to Authentication index](index.md)

# Basic authentication
HTTP Basic Auth is the most straightforward option. The client includes a
username and password in the `Authorization` header on every request. The
credentials are base64 encoded but otherwise sent in plain text, so HTTPS is
strongly recommended.
Provide a lookup field and password check method on your user model:
```
class Config(BaseConfig):
    API_AUTHENTICATE_METHOD = ["basic"]
    API_USER_MODEL = User
    API_USER_LOOKUP_FIELD = "username"
    API_CREDENTIAL_CHECK_METHOD = "check_password"
```
flarchitect also provides a simple login route for this strategy. POST to
`/auth/login` with a `Basic` `Authorization` header to verify
credentials and receive basic user information:
```
curl -X POST -u username:password http://localhost:5000/auth/login
```
You can then access endpoints with tools such as `curl`:
```
curl -u username:password http://localhost:5000/api/books
```
See `demo/authentication/basic_auth.py` for a runnable snippet.

