Authentication
=========================================

flarchitect provides several helpers so you can secure your API quickly.
Enable one or more strategies via ``API_AUTHENTICATE_METHOD``. Available
methods are ``jwt``, ``basic``, ``api_key`` and ``custom``. Each example below
uses the common setup defined in ``demo/authentication/app_base.py``.

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

``demo/authentication/jwt_auth.py`` contains a full example including a login
route:

.. code-block:: python

   from flask import abort, request
   from flask_jwt_extended import (
       create_access_token,
       create_refresh_token,
   )

   @app.post("/login")
   def login():
       user = User.query.filter_by(username=request.json["username"]).first()
       if user and user.check_password(request.json["password"]):
           return {
               "access_token": create_access_token(identity=user.id),
               "refresh_token": create_refresh_token(identity=user.id),
           }
       abort(401)

Send subsequent requests with the ``Authorization`` header set to the access
token and refresh it with the refresh token when it expires.

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
each request, usually via a header like ``X-API-Key`` or as a query string
parameter. flarchitect passes the token to a function you provide, and the
function returns the matching user.

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

Example request:

.. code-block:: bash

   curl -H "X-API-Key: <token>" http://localhost:5000/api/books

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
