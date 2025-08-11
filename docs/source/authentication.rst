Authentication
=========================================

flarchitect ships with multiple authentication helpers so you can secure your
API quickly. Enable one or more strategies via the ``API_AUTHENTICATE_METHOD``
configuration value. The available methods are ``jwt``, ``basic``, ``api_key``
and ``custom``. Each example below shares a common setup defined in
``demo/authentication/app_base.py``.

JWT tokens
----------

Requires ``ACCESS_SECRET_KEY`` and ``REFRESH_SECRET_KEY`` as well as a user
model. A minimal configuration looks like:

.. code-block:: python

   class Config(BaseConfig):
       API_AUTHENTICATE_METHOD = ["jwt"]
       ACCESS_SECRET_KEY = "access-secret"
       REFRESH_SECRET_KEY = "refresh-secret"
       API_USER_MODEL = User
       API_USER_LOOKUP_FIELD = "username"
       API_CREDENTIAL_CHECK_METHOD = "check_password"

See ``demo/authentication/jwt_auth.py`` for a full example including a login
endpoint.

Basic authentication
--------------------

Provide a lookup field and password check method on your user model:

.. code-block:: python

   class Config(BaseConfig):
       API_AUTHENTICATE_METHOD = ["basic"]
       API_USER_MODEL = User
       API_USER_LOOKUP_FIELD = "username"
       API_CREDENTIAL_CHECK_METHOD = "check_password"

A runnable snippet lives at ``demo/authentication/basic_auth.py``.

API key authentication
----------------------

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

See ``demo/authentication/api_key_auth.py`` for more detail.

Custom authentication
---------------------

For complete control supply your own callable:

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

The ``demo/authentication/custom_auth.py`` module shows this approach in
context.
