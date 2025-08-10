Authentication
=========================================

flarchitect ships with simple JWT helpers so you can secure your API quickly.

* ``generate_access_token`` and ``generate_refresh_token`` create tokens for your users.
* ``refresh_access_token`` issues a new access token when the old one expires.
* ``jwt_authentication`` decorator validates incoming tokens and populates the current user.

Tokens require ``ACCESS_SECRET_KEY`` and ``REFRESH_SECRET_KEY`` to be set and a user model specified via configuration.
Check the demo application for a complete example.
