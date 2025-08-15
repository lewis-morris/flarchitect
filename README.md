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

### Optional extras

- **Rate limiting & structured responses** – configurable throttling and consistent response schema.
- **Field validation** – built-in validators for emails, URLs, IPs and more.
- **Nested writes** – send related objects in POST/PUT payloads when `API_ALLOW_NESTED_WRITES` is `True`.
- **CORS support** – enable cross-origin requests with `API_ENABLE_CORS`.

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

flarchitect ships with ready-to-use JWT, Basic and API key authentication. Choose strategies with
`API_AUTHENTICATE_METHOD`.

### JWT

```python
app.config["API_AUTHENTICATE_METHOD"] = ["jwt"]
app.config["ACCESS_SECRET_KEY"] = "access-secret"
app.config["REFRESH_SECRET_KEY"] = "refresh-secret"
app.config["API_USER_MODEL"] = User
app.config["API_USER_LOOKUP_FIELD"] = "username"
app.config["API_CREDENTIAL_CHECK_METHOD"] = "check_password"
```

### Basic

```python
app.config["API_AUTHENTICATE_METHOD"] = ["basic"]
app.config["API_USER_MODEL"] = User
app.config["API_USER_LOOKUP_FIELD"] = "username"
app.config["API_CREDENTIAL_CHECK_METHOD"] = "check_password"
```

### API key

```python
app.config["API_AUTHENTICATE_METHOD"] = ["api_key"]
app.config["API_KEY_AUTH_AND_RETURN_METHOD"] = lookup_user_by_token
# app.config["API_CREDENTIAL_HASH_FIELD"] = "api_key_hash"  # optional
```

See the [authentication docs](docs/source/authentication.rst) for full configuration details and custom strategies.

## OpenAPI specification

An OpenAPI 3 schema is generated automatically and powers the Redoc UI. You
can switch to Swagger‑UI by setting ``API_DOCS_STYLE = 'swagger'`` in your Flask
config. Either way you can serve the raw specification to integrate with
tooling such as Postman:

```python
from flask import Flask
from flarchitect import Architect

app = Flask(__name__)
architect = Architect(app)  # OpenAPI served at /openapi.json, docs served at /docs

```

The specification endpoint can be customised with ``API_SPEC_ROUTE``. See the
[OpenAPI docs](docs/source/openapi.rst) for exporting or customising the
document.

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

## Versioning & Releases

The package version is defined in `pyproject.toml` and exposed as `flarchitect.__version__`. A GitHub Actions workflow automatically publishes to PyPI when the version changes on `master`.

To publish a new release:

1. Commit your feature or fix.
2. Run `bumpwright auto --commit --tag` to let BumpWright calculate the next version and record it in a separate commit (and tag).
3. Push both your feature commit and the bump commit (along with any tags) to `master`.

Ensure the repository has a `PYPI_API_TOKEN` secret with an API token from PyPI.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

