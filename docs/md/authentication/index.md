# Authentication

flarchitect provides several helpers to secure your API quickly. Enable one or
more strategies via API_AUTHENTICATE_METHOD <configuration.html#AUTHENTICATE_METHOD>.
Available methods are `jwt`, `basic`, `api_key` and `custom`.
Each example below uses the common setup defined in
`demo/authentication/app_base.py`. Runnable snippets demonstrating each
strategy live in the project repository: jwt_auth.py, basic_auth.py,
api_key_auth.py, and custom_auth.py. You can also protect routes based on
user roles using the `require_roles` decorator.
| Method | Required config keys | Demo |
| --- | --- | --- |
| `jwt` | `ACCESS_SECRET_KEY`, `REFRESH_SECRET_KEY`, API_USER_MODEL <configuration.html#USER_MODEL>, API_USER_LOOKUP_FIELD <configuration.html#USER_LOOKUP_FIELD>, API_CREDENTIAL_CHECK_METHOD <configuration.html#CREDENTIAL_CHECK_METHOD> | jwt_auth.py |
| `basic` | API_USER_MODEL <configuration.html#USER_MODEL>, API_USER_LOOKUP_FIELD <configuration.html#USER_LOOKUP_FIELD>, API_CREDENTIAL_CHECK_METHOD <configuration.html#CREDENTIAL_CHECK_METHOD> | basic_auth.py |
| `api_key` | API_KEY_AUTH_AND_RETURN_METHOD <configuration.html#KEY_AUTH_AND_RETURN_METHOD> (or API_CREDENTIAL_HASH_FIELD <configuration.html#CREDENTIAL_HASH_FIELD> + API_CREDENTIAL_CHECK_METHOD <configuration.html#CREDENTIAL_CHECK_METHOD>) | api_key_auth.py |
| `custom` | API_CUSTOM_AUTH <configuration.html#CUSTOM_AUTH> | custom_auth.py |

## Sections

- [Error responses](error-responses.md)
- [JWT authentication](jwt-authentication.md)
- [Basic authentication](basic-authentication.md)
- [API key authentication](api-key-authentication.md)
- [Custom authentication](custom-authentication.md)
- [Role-based access](role-based-access.md)
- [Config-driven roles](config-driven-roles.md)
- [Troubleshooting](troubleshooting.md)
