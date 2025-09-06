Authentication
=========================================

flarchitect provides several helpers to secure your API quickly. Enable one or
more strategies via `API_AUTHENTICATE_METHOD <configuration.html#AUTHENTICATE_METHOD>`_.
Available methods are ``jwt``, ``basic``, ``api_key`` and ``custom``.

Each example below uses the common setup defined in
``demo/authentication/app_base.py``. Runnable snippets demonstrating each
strategy live in the project repository: `jwt_auth.py`_, `basic_auth.py`_,
`api_key_auth.py`_, and `custom_auth.py`_. You can also protect routes based on
user roles using the ``require_roles`` decorator.

.. list-table:: Authentication methods
   :header-rows: 1

   * - Method
     - Required config keys
     - Demo
   * - ``jwt``
     - ``ACCESS_SECRET_KEY``, ``REFRESH_SECRET_KEY``, `API_USER_MODEL <configuration.html#USER_MODEL>`_, `API_USER_LOOKUP_FIELD <configuration.html#USER_LOOKUP_FIELD>`_, `API_CREDENTIAL_CHECK_METHOD <configuration.html#CREDENTIAL_CHECK_METHOD>`_
     - `jwt_auth.py`_
   * - ``basic``
     - `API_USER_MODEL <configuration.html#USER_MODEL>`_, `API_USER_LOOKUP_FIELD <configuration.html#USER_LOOKUP_FIELD>`_, `API_CREDENTIAL_CHECK_METHOD <configuration.html#CREDENTIAL_CHECK_METHOD>`_
     - `basic_auth.py`_
   * - ``api_key``
     - `API_KEY_AUTH_AND_RETURN_METHOD <configuration.html#KEY_AUTH_AND_RETURN_METHOD>`_ (or `API_CREDENTIAL_HASH_FIELD <configuration.html#CREDENTIAL_HASH_FIELD>`_ + `API_CREDENTIAL_CHECK_METHOD <configuration.html#CREDENTIAL_CHECK_METHOD>`_)
     - `api_key_auth.py`_
   * - ``custom``
     - `API_CUSTOM_AUTH <configuration.html#CUSTOM_AUTH>`_
     - `custom_auth.py`_

Error responses
---------------

Authentication failures are serialised with :func:`create_response`, so each
payload includes standard metadata like the API version, timestamp and response
time.

Missing or invalid credentials return a ``401``:

.. code-block:: json

    {
      "api_version": "0.1.0",
      "datetime": "2024-01-01T00:00:00+00:00",
      "status_code": 401,
      "errors": {"error": "Unauthorized", "reason": "Authorization header missing"},
      "response_ms": 5.0,
      "total_count": 1,
      "next_url": null,
      "previous_url": null,
      "value": null
    }

Expired tokens also yield a ``401``:

.. code-block:: json

    {
      "api_version": "0.1.0",
      "datetime": "2024-01-01T00:00:00+00:00",
      "status_code": 401,
      "errors": {"error": "Unauthorized", "reason": "Token has expired"},
      "response_ms": 5.0,
      "total_count": 1,
      "next_url": null,
      "previous_url": null,
      "value": null
    }

Refresh failures fall into two categories:

- Invalid refresh JWT (bad format, wrong signature, wrong ``iss``/``aud``) → ``401`` with reason ``Invalid token``.
- Unknown, revoked or expired-in-store refresh token → ``403`` with reason ``Invalid or expired refresh token``.

Example ``403`` response:

.. code-block:: json

    {
      "api_version": "0.1.0",
      "datetime": "2024-01-01T00:00:00+00:00",
      "status_code": 403,
      "errors": {"error": "Forbidden", "reason": "Invalid or expired refresh token"},
      "response_ms": 5.0,
      "total_count": 1,
      "next_url": null,
      "previous_url": null,
      "value": null
    }

JWT authentication
------------------

JSON Web Tokens (JWT) allow a client to prove their identity by including a
signed token with every request. The token typically contains the user's ID and
an expiry timestamp. Clients obtain an access/refresh pair from a login endpoint
and then send the access token in the ``Authorization`` header:

``Authorization: Bearer <access-token>``

To enable JWT support you must provide ``ACCESS_SECRET_KEY`` and
``REFRESH_SECRET_KEY`` values along with a user model. A minimal configuration
looks like:

.. code-block:: python

    class Config(BaseConfig):
        API_AUTHENTICATE_METHOD = ["jwt"]
        ACCESS_SECRET_KEY = "access-secret"
        REFRESH_SECRET_KEY = "refresh-secret"
        API_USER_MODEL = User
        API_USER_LOOKUP_FIELD = "username"
        API_CREDENTIAL_CHECK_METHOD = "check_password"

Token lifetimes default to ``360`` minutes for access tokens and ``2880``
minutes (two days) for refresh tokens. Override these durations with
`API_JWT_EXPIRY_TIME <configuration.html#JWT_EXPIRY_TIME>`_ and `API_JWT_REFRESH_EXPIRY_TIME <configuration.html#JWT_REFRESH_EXPIRY_TIME>`_ respectively. The
default algorithm is ``HS256`` (override via
`API_JWT_ALGORITHM <configuration.html#JWT_ALGORITHM>`_). When decoding a
token, :func:`flarchitect.authentication.jwt.get_user_from_token` resolves the
secret key in this order: explicit argument → ``ACCESS_SECRET_KEY`` environment
variable → Flask config.

Hardening options
~~~~~~~~~~~~~~~~~

JWT validation can be tightened with the following settings:

- ``API_JWT_ALLOWED_ALGORITHMS``: Restrict verification to a specific set of algorithms (list or comma-separated string). Defaults to the configured algorithm.
- ``API_JWT_ISSUER`` / ``API_JWT_AUDIENCE``: Include and enforce ``iss``/``aud`` claims during encode/decode.
- ``API_JWT_LEEWAY``: Allow small clock skew (in seconds) when validating ``exp``/``iat``.
- ``API_JWT_ALGORITHM="RS256"``: Use RSA key pairs. Set ``ACCESS_PRIVATE_KEY`` and ``ACCESS_PUBLIC_KEY`` (and their ``REFRESH_*`` equivalents) with PEM strings. For compatibility, a single ``ACCESS_SECRET_KEY``/``REFRESH_SECRET_KEY`` may be used to verify if public keys are not set, but key pairs are recommended.

Token rotation and revocation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Refresh tokens are single‑use. When clients call ``POST /auth/refresh`` with a valid refresh token, the server revokes the token and issues a new access/refresh pair.
- Deny‑list and auditing: The refresh token store persists ``created_at``, ``last_used_at``, ``revoked``/``revoked_at`` and a ``replaced_by`` pointer to the next token. This provides a clear trail for incident response.
- Programmatic revocation: Administrators can revoke a specific token at any time with ``revoke_refresh_token(token)`` from ``flarchitect.authentication.token_store``.

Built‑in endpoints
~~~~~~~~~~~~~~~~~~

When JWT is enabled, flarchitect registers the following routes:

``POST /auth/login``
    Accepts JSON ``{"username": "<name>", "password": "<password>"}`` and
    returns an access/refresh token pair and the user's primary key.

``POST /auth/refresh``
    Accepts JSON ``{"refresh_token": "<token>"}`` and returns a new access
    token. For robustness, a value prefixed with ``"Bearer "`` is accepted and
    normalised (e.g., ``"Bearer <token>"``). Invalid refresh JWTs yield ``401``;
    revoked or expired-in-store tokens return ``403``.

``POST /auth/logout``
    Stateless logout that clears the user context on the server.

Clients include the access token with each request using the standard header::

   Authorization: Bearer <access-token>

Protecting manual routes
~~~~~~~~~~~~~~~~~~~~~~~~

Endpoints generated by flarchitect are automatically secured when
`API_AUTHENTICATE_METHOD <configuration.html#AUTHENTICATE_METHOD>`_ includes ``"jwt"``. If you add your own Flask routes
outside the generated API, decorate them with ``jwt_authentication`` to enforce
the same protection:

.. code-block:: python

   from flarchitect.core.architect import jwt_authentication

   @app.get("/profile")
   @jwt_authentication
   def profile() -> dict[str, str]:
       return {"status": "ok"}

This decorator reads the ``Authorization`` header, validates the token and sets
``current_user``. Automatically created endpoints do not need it because global
settings already apply authentication.

Refresh token storage
~~~~~~~~~~~~~~~~~~~~~

By default, flarchitect persists JWT refresh tokens in an SQL table named
``refresh_tokens``. The table contains four columns:

* ``token`` – the encoded refresh token (primary key)
* ``user_pk`` – the user's primary key as a string
* ``user_lookup`` – the configured user lookup value
* ``expires_at`` – the token's expiry timestamp

The table is created automatically when a refresh token is stored. You can
manage tokens directly using helpers from
``flarchitect.authentication.token_store``:

.. code-block:: python

   from datetime import datetime, timedelta, timezone
   from flarchitect.authentication.token_store import (
       delete_refresh_token,
       get_refresh_token,
       store_refresh_token,
   )

   expires = datetime.now(timezone.utc) + timedelta(days=1)
   store_refresh_token(
       "encoded-token", user_pk="1", user_lookup="alice", expires_at=expires
   )

   stored = get_refresh_token("encoded-token")
   if stored:
       print(stored.user_pk, stored.expires_at)

   delete_refresh_token("encoded-token")

Basic authentication
--------------------

HTTP Basic Auth is the most straightforward option. The client includes a
username and password in the ``Authorization`` header on every request. The
credentials are base64 encoded but otherwise sent in plain text, so HTTPS is
strongly recommended.

Provide a lookup field and password check method on your user model:

.. code-block:: python

   class Config(BaseConfig):
       API_AUTHENTICATE_METHOD = ["basic"]
       API_USER_MODEL = User
       API_USER_LOOKUP_FIELD = "username"
       API_CREDENTIAL_CHECK_METHOD = "check_password"

flarchitect also provides a simple login route for this strategy. POST to
``/auth/login`` with a ``Basic`` ``Authorization`` header to verify
credentials and receive basic user information:

.. code-block:: bash

   curl -X POST -u username:password http://localhost:5000/auth/login

You can then access endpoints with tools such as ``curl``:

.. code-block:: bash

   curl -u username:password http://localhost:5000/api/books

See ``demo/authentication/basic_auth.py`` for a runnable snippet.

API key authentication
----------------------

API key auth associates a user with a single token. Clients send the token in
each request via an ``Authorization`` header using the ``Api-Key`` scheme. The
framework passes the token to a function you provide (or validates a stored
hash) and uses the returned user for the request.
If you store hashed tokens on the model, set `API_CREDENTIAL_HASH_FIELD <configuration.html#CREDENTIAL_HASH_FIELD>`_ to the attribute holding the hash so flarchitect can validate keys.

Attach a function that accepts an API key and returns a user. The function can
also call ``set_current_user``:

.. code-block:: python

   def lookup_user_by_token(token: str) -> User | None:
       user = User.query.filter_by(api_key=token).first()
       if user:
           set_current_user(user)
       return user

   class Config(BaseConfig):
       API_AUTHENTICATE_METHOD = ["api_key"]
       API_KEY_AUTH_AND_RETURN_METHOD = staticmethod(lookup_user_by_token)

When this method is enabled flarchitect exposes a companion login route. POST
an ``Api-Key`` ``Authorization`` header to ``/auth/login`` to validate the key
and retrieve basic user details:

.. code-block:: bash

   curl -X POST -H "Authorization: Api-Key <token>" http://localhost:5000/auth/login

Clients include the API key with each request using:

.. code-block:: bash

   curl -H "Authorization: Api-Key <token>" http://localhost:5000/api/books

See ``demo/authentication/api_key_auth.py`` for more detail.

Custom authentication
---------------------

For complete control supply your own callable. This method lets you support any
authentication strategy you like: session cookies, HMAC signatures or
third-party OAuth flows. Your callable should return ``True`` on success and may
call ``set_current_user`` to attach the authenticated user to the request.

.. code-block:: python

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

Clients can then call your API with whatever headers your function expects:

.. code-block:: bash

   curl -H "X-Token: <token>" http://localhost:5000/api/books

See ``demo/authentication/custom_auth.py`` for this approach in context.

.. _roles-required:

Role-based access
-----------------

Use the ``require_roles`` decorator to restrict access based on user roles. The
decorator reads ``current_user.roles`` which is populated by the active
authentication method.

.. code-block:: python

   from flarchitect.authentication import require_roles

   @app.get("/admin")
   @require_roles("admin")
   def admin_dashboard():
       return {"status": "ok"}

Pass multiple roles to require all of them. To allow access when a user has
*any* of the listed roles, set ``any_of=True``:

.. code-block:: python

   @require_roles("admin", "editor", any_of=True)
   def update_post():
       ...

.. _defining-roles:

Defining roles
~~~~~~~~~~~~~~

Roles can be attached to the user model or embedded in authentication tokens so
``require_roles`` can evaluate permissions.

JWT
^^^^

1. Persist a ``roles`` attribute on the user model, e.g. ``User.roles = ["admin"]``.
2. ``require_roles`` reads roles from ``current_user`` after the token is
   validated and the user is loaded.

API keys
^^^^^^^^

1. Store roles on the user model.
2. In the lookup function, return a user object with those roles::

       def lookup_user_by_token(token: str) -> User | None:
           user = User.query.filter_by(api_key=token).first()
           if user:
               set_current_user(user)
           return user

3. ``require_roles`` pulls roles from ``current_user``.

Custom authentication
^^^^^^^^^^^^^^^^^^^^^

1. Resolve the user from your custom credentials.
2. Call ``set_current_user`` with an object exposing ``roles``.
3. ``require_roles`` authorises the request using those roles.

Common roles
^^^^^^^^^^^^

.. list-table:: Common roles
   :header-rows: 1

   * - Role
     - Responsibility
   * - ``admin``
     - Full access to manage resources and users.
   * - ``editor``
     - Create and modify resources but cannot manage users.
   * - ``viewer``
     - Read-only access to resources.

If the authenticated user lacks any of the required roles—or if no user is
authenticated—a ``403`` response is raised.

Config-driven roles
-------------------

You can assign roles to endpoints without decorating functions by setting a
single map in configuration or on a model's ``Meta``. This is the most
maintainable way to protect all generated CRUD routes consistently.

Use ``API_ROLE_MAP`` with method names as keys. Values may be a list of roles
that must all be present, a string for a single role, or a dictionary with an
``any_of`` flag for “any of these roles” semantics.

Global example (applies to all models):

.. code-block:: python

   app.config.update(
       API_AUTHENTICATE_METHOD=["jwt"],  # ensure authentication is enabled
       API_ROLE_MAP={
           "GET": ["viewer"],                  # both list & string forms are accepted
           "POST": {"roles": ["editor", "admin"], "any_of": True},
           "PATCH": ["editor", "admin"],       # require all listed roles
           "DELETE": ["admin"],
           "ALL": True,                         # optional: means "auth-only" for any unspecified methods
       },
   )

Model-specific example (overrides global for this model only):

.. code-block:: python

   class Book(Base):
       __tablename__ = "books"

       class Meta:
           api_role_map = {
               "GET_MANY": ["viewer"],
               "GET_ONE": ["viewer"],
               "POST": ["editor"],
               "PATCH": {"roles": ["editor", "admin"], "any_of": True},
               "DELETE": ["admin"],
           }

Recognised keys
~~~~~~~~~~~~~~~~

- ``GET``, ``POST``, ``PATCH``, ``DELETE``: Protects the corresponding CRUD endpoints.
- ``GET_MANY`` / ``GET_ONE``: Optional split for collection vs single-item GET.
- ``RELATION_GET``: Protects relation endpoints like ``/parents/{id}/children``.
- ``ALL`` or ``*``: Fallback applied when a method key is not present.

Fallbacks
~~~~~~~~~

If you prefer very simple policies, instead of ``API_ROLE_MAP`` you can set one
of the following (globally or on a model's ``Meta``):

- ``API_ROLES_REQUIRED``: list of roles, all must be present.
- ``API_ROLES_ACCEPTED``: list of roles where any grants access.

These apply to all endpoints for that model and are overridden by
``API_ROLE_MAP`` when both are present.

Troubleshooting
---------------

.. list-table::
   :header-rows: 1

   * - Problem
     - Solution
   * - Missing Authorization header
     - Include the appropriate ``Authorization`` header with your credentials.
   * - Token has expired
     - Use the refresh token to obtain a new access token.
   * - Invalid or expired refresh token
     - Log in again to receive a new access/refresh token pair.


.. _jwt_auth.py: https://github.com/lewis-morris/flarchitect/blob/master/demo/authentication/jwt_auth.py
.. _basic_auth.py: https://github.com/lewis-morris/flarchitect/blob/master/demo/authentication/basic_auth.py
.. _api_key_auth.py: https://github.com/lewis-morris/flarchitect/blob/master/demo/authentication/api_key_auth.py
.. _custom_auth.py: https://github.com/lewis-morris/flarchitect/blob/master/demo/authentication/custom_auth.py
