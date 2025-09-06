# flarchitect

[![Docs](https://github.com/lewis-morris/flarchitect/actions/workflows/docs.yml/badge.svg?branch=master)](https://github.com/lewis-morris/flarchitect/actions/workflows/docs.yml)
[![Tests](https://github.com/lewis-morris/flarchitect/actions/workflows/run-unit-tests.yml/badge.svg?branch=master&event=push)](https://github.com/lewis-morris/flarchitect/actions/workflows/run-unit-tests.yml)
![Coverage](https://lewis-morris.github.io/flarchitect/_static/coverage.svg)
[![PyPI version](https://img.shields.io/pypi/v/flarchitect.svg)](https://pypi.org/project/flarchitect/)



flarchitect is a friendly Flask extension that turns your SQLAlchemy or Flask-SQLAlchemy models into a production-ready REST API in minutes while keeping you in full control of your models and endpoints. It automatically builds CRUD endpoints, generates interactive Redoc documentation and keeps responses consistent so you can focus on your application logic.

## Why flarchitect?

If you're new here, welcome! flarchitect gets you from data models to a fully fledged REST API in minutes, saving you time without sacrificing quality or customisation.

## Features

- **Automatic CRUD endpoints** – expose SQLAlchemy models as RESTful resources with a simple `Meta` class.
- **Interactive documentation** – Redoc or Swagger UI generated at runtime and kept in sync with your models.
- **Built-in authentication** – JWT, basic and API key strategies ship with a ready‑made `/auth/login` endpoint, or plug in your own.
- **Extensibility hooks** – customise request and response flows.
- **Soft delete** – hide and restore records without permanently removing them.
- **GraphQL integration** – expose your models through a single `/graphql` endpoint when you need more flexible queries.

### Performance & Observability

- **Request-local config caching** – repeated calls to resolve config/model meta are cached per request to reduce overhead.
- **Schema class caching** – dynamic schema classes and subclass lookups are cached to skip repeated reflection.
- **Correlation IDs** – every response includes `X-Request-ID` (propagates inbound header when present).
- **Structured logs (optional)** – JSON logs include method, path, status, latency and `request_id`.

### Optional extras

- **Rate limiting & structured responses** – configurable throttling and consistent response schema.
- **Field validation** – built-in validators for emails, URLs, IPs and more.
- **Nested writes** – send related objects in POST/PUT payloads when `API_ALLOW_NESTED_WRITES` is `True`.
- **CORS support** – enable cross-origin requests with `API_ENABLE_CORS`.

### Real-time updates (optional)

Enable lightweight WebSocket broadcasts for CRUD changes:

```python
app.config.update(
    API_ENABLE_WEBSOCKETS=True,
    API_WEBSOCKET_PATH="/ws",  # optional
)
```

Install the optional dependency: `pip install flask-sock`. Clients can connect
to `ws://<host>/ws?topic=<model>` (or omit `topic` to receive all events).
See the docs page “WebSockets” for details and examples.

## Installation

flarchitect supports Python 3.10 and newer. Set up a virtual environment, install the package and verify the install:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install flarchitect
python -c "import flarchitect; print(flarchitect.__version__)"
```

The final command prints the version number to confirm everything installed correctly.

## Quick Start

```python
from flask import Flask
from flarchitect import Architect
from models import Author, BaseModel  # your SQLAlchemy models

app = Flask(__name__)
app.config["API_TITLE"] = "My API"
app.config["API_VERSION"] = "1.0"
app.config["API_BASE_MODEL"] = BaseModel
app.config["API_ALLOW_NESTED_WRITES"] = True

architect = Architect(app)

if __name__ == "__main__":
    app.run(debug=True)
```

With the application running, try your new API in another terminal window:

```bash
curl http://localhost:5000/api/authors
```

## Authentication

flarchitect ships with ready‑to‑use JWT, Basic and API key authentication. Enable one or more strategies with
`API_AUTHENTICATE_METHOD`.

What you get out of the box:

- A set of `/auth` endpoints when JWT is enabled: `/auth/login`, `/auth/logout`, `/auth/refresh`.
- Consistent error responses (HTTP 401/403) with a clear `reason` string.
- Helpers for per‑route protection and role checks.

### JWT

Configuration (the minimal set):

```python
app.config.update(
    API_AUTHENTICATE_METHOD=["jwt"],
    ACCESS_SECRET_KEY="access-secret",     # or set env var ACCESS_SECRET_KEY
    REFRESH_SECRET_KEY="refresh-secret",   # or set env var REFRESH_SECRET_KEY
    API_USER_MODEL=User,                    # your SQLAlchemy model
    API_USER_LOOKUP_FIELD="username",      # field used to find the user
    API_CREDENTIAL_CHECK_METHOD="check_password",  # method on User to verify password
)
```

Endpoints and payloads:

- `POST /auth/login` with JSON `{"username": "alice", "password": "secret"}` returns
  `{ "access_token": "...", "refresh_token": "...", "user_pk": 1 }` on success.
- `POST /auth/refresh` with JSON `{ "refresh_token": "..." }` returns a new access token. A leading `"Bearer "` prefix is tolerated and removed. Invalid refresh JWTs return `401`; unknown/revoked/expired refresh tokens return `403`.
- `POST /auth/logout` clears user context (stateless logout; refresh tokens are invalidated on use/expiry).

Protecting routes:

- Via decorator: `from flarchitect.core.architect import jwt_authentication` and decorate the view: `@jwt_authentication`.
- Via schema wrapper: `@architect.schema_constructor(output_schema=..., auth=True)` when generating routes with Architect.

Token settings and key resolution:

- Access token lifetime: `API_JWT_EXPIRY_TIME` (minutes, default `360`).
- Refresh token lifetime: `API_JWT_REFRESH_EXPIRY_TIME` (minutes, default `2880`).
- Algorithm: `API_JWT_ALGORITHM` (`HS256` by default). To restrict verification to specific algorithms, set `API_JWT_ALLOWED_ALGORITHMS` (list or comma‑separated string).
- Issuer and audience: set `API_JWT_ISSUER` and/or `API_JWT_AUDIENCE` to include and enforce `iss`/`aud` claims.
- Clock skew: allow small time drift during verification with `API_JWT_LEEWAY` (seconds, default `0`).
- RS256 support: when `API_JWT_ALGORITHM="RS256"`, sign with `ACCESS_PRIVATE_KEY` and verify with `ACCESS_PUBLIC_KEY` (PEM strings). Refresh tokens use `REFRESH_PRIVATE_KEY`/`REFRESH_PUBLIC_KEY`. For backwards compatibility, if only `ACCESS_SECRET_KEY`/`REFRESH_SECRET_KEY` are provided they are used to verify, but key pairs are recommended.
- `get_user_from_token(secret_key=...)` secret selection order: explicit argument > `ACCESS_SECRET_KEY` env var > Flask `ACCESS_SECRET_KEY` config (or public key when using RS*).

Refresh token rotation and revocation:

- Refresh tokens are single‑use: calling `/auth/refresh` revokes the old refresh token and issues a new one.
- Revocation (deny‑list) and auditing: the refresh token store records `created_at`, `last_used_at`, `revoked`, `revoked_at`, and links to the `replaced_by` token for traceability. Admins can revoke tokens programmatically via `flarchitect.authentication.token_store.revoke_refresh_token`.

### Basic

```python
app.config.update(
    API_AUTHENTICATE_METHOD=["basic"],
    API_USER_MODEL=User,
    API_USER_LOOKUP_FIELD="username",
    API_CREDENTIAL_CHECK_METHOD="check_password",
)
```

Usage: send an `Authorization: Basic <base64(username:password)>` header. You can also protect routes via
`@architect.schema_constructor(..., auth=True)`.

### API key

Two options:

1) Provide a custom lookup function that both authenticates and returns the user:

```python
def lookup_user_by_token(token: str) -> User | None:
    return User.query.filter_by(api_key=token).first()

app.config.update(
    API_AUTHENTICATE_METHOD=["api_key"],
    API_KEY_AUTH_AND_RETURN_METHOD=staticmethod(lookup_user_by_token),
)
```

2) Or use a hashed field and a verification method on the model:

```python
app.config.update(
    API_AUTHENTICATE_METHOD=["api_key"],
    API_USER_MODEL=User,
    API_CREDENTIAL_HASH_FIELD="api_key_hash",
    API_CREDENTIAL_CHECK_METHOD="check_api_key",
)
```

Usage: send an `Authorization: Api-Key <token>` header.

Role‑based access control:

```python
from flarchitect.authentication import require_roles

@app.get("/admin")
@jwt_authentication
@require_roles("admin")
def admin_panel():
    ...
```

You can also protect all generated CRUD routes without decorators using a
config‑driven map:

```python
app.config.update(
    API_AUTHENTICATE_METHOD=["jwt"],
    API_ROLE_MAP={
        "GET": ["viewer"],
        "POST": {"roles": ["editor", "admin"], "any_of": True},
        "DELETE": ["admin"],
    },
)
```

See docs: Authentication → Role‑based access → Config‑driven roles.

See the full Authentication guide in the hosted docs for advanced configuration and custom strategies.

## OpenAPI specification

An OpenAPI 3 schema is generated automatically and powers the Redoc UI. You
can switch to Swagger‑UI by setting ``API_DOCS_STYLE = 'swagger'`` in your Flask
config. Either way you can serve the raw specification to integrate with
tooling such as Postman:

```python
from flask import Flask
from flarchitect import Architect

app = Flask(__name__)
architect = Architect(app)  # Docs at /docs; JSON spec at /docs/apispec.json (canonical)

```

The canonical JSON for the docs UI is configurable via ``API_DOCS_SPEC_ROUTE`` (default ``/docs/apispec.json``).
The legacy top‑level ``API_SPEC_ROUTE`` (default ``/openapi.json``) now redirects to the docs JSON and will be removed in a future release.
See the [OpenAPI docs](docs/source/openapi.rst) for exporting or customising the document.

## Performance: Caching

Two low-risk caches improve request throughput without changing public APIs:

- Config/meta cache: `get_config_or_model_meta` caches positive lookups per request.
  This avoids repeated Flask config and model `Meta` introspection during routing,
  schema generation and auth checks.
- Schema class cache: dynamic schema classes and subclass lookups are memoised at
  module level. Schema instances are still created per call so request-specific
  options (e.g. `join`, `dump_relationships`, recursion depth) remain correct.

No configuration is required to enable these caches. They are safe in multi-threaded
environments and reset naturally between requests.

## Observability: Request IDs and JSON logs

Every request is assigned a correlation ID and returned via the `X-Request-ID`
response header. If a client sends its own `X-Request-ID`, that value is propagated.
To also include the correlation ID in the JSON response body, opt in with:

```python
app.config["API_DUMP_REQUEST_ID"] = True  # default False
```

Enable structured JSON logs for production:

```python
app.config.update(
    API_JSON_LOGS=True,       # emit JSON lines with context
    API_VERBOSITY_LEVEL=1,    # 0=quiet, higher=more verbose
    API_LOG_REQUESTS=True,    # default True; per-request completion log
)
```

Example log line (pretty-printed for readability):

```
{
  "event": "log",
  "lvl": 1,
  "message": "Completed GET /api/items -> 200",
  "method": "GET",
  "path": "/api/items",
  "request_id": "e5f9c0c8f2ac4c58b6a1c5b6d8d3e9a1",
  "latency_ms": 12
}
```

When `API_JSON_LOGS` is `False` (default), logs are colourised for humans and the
`X-Request-ID` header remains available for correlation.

## GraphQL

Prefer working with a single endpoint? `flarchitect` can turn your SQLAlchemy
models into a GraphQL schema with just a couple of lines. Generate the schema
and register it with the architect:

```python
from flarchitect.graphql import create_schema_from_models

schema = create_schema_from_models([Item], db.session)
architect.init_graphql(schema=schema)
```

The generated schema exposes CRUD-style queries and mutations for each model,
including `all_items`, `item`, `create_item`, `update_item` and `delete_item`.
Column-level filtering and simple pagination are built in via arguments on the
`all_<table>` queries:

```graphql
query {
    all_items(name: "Foo", limit: 10, offset: 0) {
        id
        name
    }
}
```
Mutations manage records:

```graphql
mutation {
    update_item(id: 1, name: "Bar") {
        id
        name
    }
}

mutation {
    delete_item(id: 1)
}
```

Custom SQLAlchemy types can be mapped to Graphene scalars by supplying a
`type_mapping` override:

```python
schema = create_schema_from_models(
    [Item], db.session, type_mapping={MyType: graphene.String}
)
```

Run your app and open
[GraphiQL](https://github.com/graphql/graphiql) at
`http://localhost:5000/graphql` to explore your data interactively. A browser
visit issues a `GET` request that serves the GraphiQL interface, while `POST`
requests accept GraphQL operations as JSON.

Quick start:

```bash
pip install flarchitect
python app.py  # start your Flask app
# then visit http://localhost:5000/graphql
```

The [GraphQL demo](demo/graphql/README.md) contains ready-made models and
sample queries to help you get started. Read the
[detailed GraphQL docs](https://lewis-morris.github.io/flarchitect/graphql.html)
for advanced usage and configuration options.

Read about hiding and restoring records in the [soft delete section](docs/source/advanced_configuration.rst#soft-delete).

## Running Tests

To run the test suite locally:

```bash
pip install -e .[dev]
export ACCESS_SECRET_KEY=access
export REFRESH_SECRET_KEY=refresh
pytest
```

The `ACCESS_SECRET_KEY` and `REFRESH_SECRET_KEY` environment variables are required for JWT-related tests. Adjust the export
commands for your shell and operating system.

## Documentation & help

- Browse the [full documentation](https://lewis-morris.github.io/flarchitect/) for tutorials and API reference.
- Explore runnable examples in the [demo](https://github.com/lewis-morris/flarchitect/tree/master/demo) directory, including a [validators example](demo/validators/README.md) showcasing email and URL validation.
- Authentication demos: [JWT](demo/authentication/jwt_auth.py), [Basic](demo/authentication/basic_auth.py) and [API key](demo/authentication/api_key_auth.py) snippets showcase the built-in strategies.
- Questions? Join the [GitHub discussions](https://github.com/lewis-morris/flarchitect/discussions) or open an [issue](https://github.com/lewis-morris/flarchitect/issues).
- See the [changelog](CHANGELOG.md) for release history.

## Roadmap

Check out the [project roadmap](docs/source/roadmap.rst) for upcoming features and enhancements.

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

Before submitting a pull request, ensure that development dependencies are installed and linters and tests pass locally:

```bash
pip install -e .[dev]
ruff --fix .
export ACCESS_SECRET_KEY=access
export REFRESH_SECRET_KEY=refresh
pytest
```

To run tests with coverage (HTML + XML reports), use:

```bash
bash scripts/coverage.sh
```

## Versioning & Releases

The package version is defined in `pyproject.toml` and exposed as `flarchitect.__version__`. A GitHub Actions workflow automatically publishes to PyPI when the version changes on `master`.

To publish a new release:

1. Update the `version` field in `pyproject.toml` (for example with `hatch version patch`).
2. Commit and push to `master`.

Ensure the repository has a `PYPI_API_TOKEN` secret with an API token from PyPI.

## UK English API Names

This project now uses UK English spellings for public helpers while maintaining backwards‑compatible aliases:

- `deserialise_data` (alias: `deserialize_data`)
- `serialise_output_with_mallow` (alias: `serialize_output_with_mallow`)
- `standardise_response` (alias: `standardize_response`)
- `initialise_spec_template` (alias: `initialize_spec_template`)
- `handle_authorisation` (alias: `handle_authorization`)
- `AttributeInitialiserMixin` (alias class of `AttributeInitializerMixin`)

Existing code using the US spellings continues to work. Prefer the UK forms in new code and documentation.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
