Auth Cookbook
=============

This cookbook collects practical authentication patterns for flarchitect
projects. It complements the reference :doc:`authentication` guide with
end‑to‑end snippets that you can copy, adapt and deploy.

Contents
--------

* JWT patterns (HS256 and RS256, refresh, rotation)
* Basic authentication
* API key strategies (lookup function vs. hashed field)
* Role mapping examples (decorators and config‑driven)
* Multi‑tenant considerations (claims, scoping, isolation)


JWT patterns
------------

Minimal configuration::

    app.config.update(
        API_AUTHENTICATE_METHOD=["jwt"],
        ACCESS_SECRET_KEY=os.environ["ACCESS_SECRET_KEY"],
        REFRESH_SECRET_KEY=os.environ["REFRESH_SECRET_KEY"],
        API_USER_MODEL=User,
        API_USER_LOOKUP_FIELD="username",
        API_CREDENTIAL_CHECK_METHOD="check_password",
        API_JWT_EXPIRY_TIME=360,             # minutes
        API_JWT_REFRESH_EXPIRY_TIME=2880,    # minutes
        API_JWT_ALLOWED_ALGORITHMS=["HS256"],
    )

Endpoints:

* ``POST /auth/login`` → returns ``access_token`` and ``refresh_token``.
* ``POST /auth/refresh`` → accepts JSON ``{"refresh_token": "<token>"}`` (a
  leading ``"Bearer "`` prefix is tolerated and removed), then rotates the
  refresh token and issues a new access token. Invalid refresh JWTs respond
  with ``401``; unknown/revoked/expired refresh tokens respond with ``403``.
* ``POST /auth/logout`` → clears user context (stateless logout).

Key rotation with RS256
~~~~~~~~~~~~~~~~~~~~~~~

Prefer asymmetric keys in production. Keep multiple active keys and use
``kid`` headers for selection::

    app.config.update(
        API_AUTHENTICATE_METHOD=["jwt"],
        API_JWT_ALGORITHM="RS256",
        # Current signing keys (PEM strings). Store via secrets, not in code.
        ACCESS_PRIVATE_KEY=os.environ["ACCESS_PRIVATE_KEY"],
        REFRESH_PRIVATE_KEY=os.environ["REFRESH_PRIVATE_KEY"],
        # Verification keys (public). Support multiple for rotation.
        ACCESS_PUBLIC_KEY=os.environ["ACCESS_PUBLIC_KEY"],
        REFRESH_PUBLIC_KEY=os.environ["REFRESH_PUBLIC_KEY"],
        API_JWT_ALLOWED_ALGORITHMS=["RS256"],
    )

When issuing tokens, include a ``kid`` header and keep a small in‑memory map of
active public keys. Rotate by introducing a new keypair, marking the old public
key as still valid for verification, then retiring it after all issued tokens
expire. See :ref:`authentication` for claim settings (``iss``, ``aud``,
``leeway``).

Production tips
~~~~~~~~~~~~~~~

* Store secrets in environment variables or file‑based secrets mounted into the
  container. Never commit secrets to source control.
* Restrict algorithms via ``API_JWT_ALLOWED_ALGORITHMS``; set ``iss`` and
  ``aud`` claims and validate them for defence in depth.
* Keep refresh tokens single‑use (default) and log rotation events for audit.


Basic authentication
--------------------

Simple username/password verification against your user model::

    app.config.update(
        API_AUTHENTICATE_METHOD=["basic"],
        API_USER_MODEL=User,
        API_USER_LOOKUP_FIELD="username",
        API_CREDENTIAL_CHECK_METHOD="check_password",
    )

Send ``Authorization: Basic <base64(username:password)>``. Protect specific
routes with ``@architect.schema_constructor(..., auth=True)`` or global configs.


API key strategies
------------------

Lookup function (flexible)::

    def lookup_user_by_token(token: str) -> User | None:
        return User.query.filter_by(api_key=token).first()

    app.config.update(
        API_AUTHENTICATE_METHOD=["api_key"],
        API_KEY_AUTH_AND_RETURN_METHOD=staticmethod(lookup_user_by_token),
    )

Hashed field (safer at rest)::

    app.config.update(
        API_AUTHENTICATE_METHOD=["api_key"],
        API_USER_MODEL=User,
        API_CREDENTIAL_HASH_FIELD="api_key_hash",
        API_CREDENTIAL_CHECK_METHOD="check_api_key",
    )

Clients send ``Authorization: Api-Key <token>``.


Role mapping examples
---------------------

Decorator‑based RBAC::

    from flarchitect.authentication import require_roles
    from flarchitect.core.architect import jwt_authentication

    @app.get("/admin")
    @jwt_authentication
    @require_roles("admin")
    def admin_panel():
        ...

Config‑driven roles (no decorators)::

    app.config.update(
        API_AUTHENTICATE_METHOD=["jwt"],
        API_ROLE_MAP={
            "GET": ["viewer"],
            "POST": {"roles": ["editor", "admin"], "any_of": True},
            "PATCH": ["editor", "admin"],
            "DELETE": ["admin"],
            # Optional catch‑all to require auth for unspecified methods
            "ALL": True,
        },
    )

See :ref:`roles-required` and the reference :doc:`authentication` for details.


Multi‑tenant considerations
---------------------------

Claims & token shape
~~~~~~~~~~~~~~~~~~~~

Include a tenant identifier in JWTs and validate it on requests::

    # When issuing tokens
    payload = {"sub": user.id, "tenant_id": user.tenant_id, "roles": user.roles}

    # During request handling (pseudo‑code)
    @jwt_authentication
    def view():
        tenant_id = current_user.tenant_id  # derived from token/user
        # Apply tenant scope to queries
        items = Item.query.filter_by(tenant_id=tenant_id).all()

Scoping and isolation
~~~~~~~~~~~~~~~~~~~~~

* Persist ``tenant_id`` on tenant‑owned models; enforce it in query helpers or
  via a session/mapper event so all generated endpoints auto‑scope results.
* For config‑driven roles, ensure roles are interpreted within the tenant’s
  context (e.g., ``admin`` within a tenant, not globally).
* Consider per‑tenant issuers (``iss``) or audiences (``aud``) to improve
  validation and separate concerns across tenants.

Operational practices
~~~~~~~~~~~~~~~~~~~~~

* Key management: rotate signing keys without cross‑tenant leakage; prefer
  centralised JWKS with short cache TTLs if using multiple issuers.
* Testing: add property tests that randomly mix tenants to catch cross‑tenant
  access regressions.
* Logging: include ``tenant_id`` in structured logs for traceability.


Further reading
---------------

* Reference guide: :doc:`authentication`
* Configuration: :doc:`configuration`
* Error handling: :doc:`error_handling`
