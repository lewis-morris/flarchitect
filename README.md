# flarchitect

[![Docs](https://github.com/lewis-morris/flarchitect/actions/workflows/build-docs-and-push.yml/badge.svg?branch=master)](https://github.com/lewis-morris/flarchitect/actions/workflows/build-docs-and-push.yml)

flarchitect is a friendly Flask extension that turns your SQLAlchemy or Flask-SQLAlchemy models into a production-ready REST API with almost no boilerplate. It automatically builds CRUD endpoints, generates interactive Redoc documentation and keeps responses consistent so you can focus on your application logic.

## Features

- **Zero-configuration endpoints** – expose models as RESTful resources by adding a simple `Meta` class.
- **Automatic documentation** – comprehensive Redoc docs are generated at runtime and stay in sync with your models.
- **SQLAlchemy integration** – works with plain SQLAlchemy or Flask-SQLAlchemy.
- **Built-in authentication** – ship with JWT, basic and API key strategies out of the box, or plug in your own authentication.
- **Rate limiting & structured responses** – configurable throttling and responses with a consistent schema.
- **Highly configurable** – tweak behaviour globally via Flask config or per model with `Meta` attributes.
- **Nested writes** – opt-in support for sending related objects in POST/PUT payloads. Enable with `API_ALLOW_NESTED_WRITES = True` and let `AutoSchema` deserialize them automatically.

## Installation

```bash
pip install flarchitect
```

## Quick Start

```python
from flask import Flask
from flarchitect.core.architect import Architect
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

## Running Tests

To run the test suite locally:

```bash
pytest
```

## Documentation & help

- Browse the [full documentation](docs/source/index.rst) for tutorials and API reference.
- Explore runnable examples in the [demo](https://github.com/arched-dev/flarchitect/tree/master/demo) directory.
- Questions? Join the [GitHub discussions](https://github.com/arched-dev/flarchitect/discussions) or open an [issue](https://github.com/arched-dev/flarchitect/issues).

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

Before submitting a pull request, ensure that linters and tests pass locally:

```bash
ruff --fix .
pytest
```

