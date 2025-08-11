# flarchitect

flarchitect is a Flask extension that turns your SQLAlchemy models into a fully fledged REST API with minimal boilerplate. It automatically builds CRUD endpoints, generates Redoc documentation and keeps responses consistent so you can focus on your application logic.

## Features

- **Automatic endpoint creation** – expose models as RESTful resources by simply adding a `Meta` class with tags.
- **JWT authentication** – issue access and refresh tokens and protect endpoints with decorators.
- **Rate limiting support** – configure global or per-endpoint limits using `flask-limiter` with optional Redis, Memcached or MongoDB backends.
- **Structured responses** – all responses share a common format including metadata and pagination details.
- **Extensive configuration** – customise behaviour via Flask config or per-model settings.
- **Redoc documentation** – interactive documentation is generated at runtime from your models and configuration.

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

architect = Architect(app)

if __name__ == "__main__":
    app.run(debug=True)
```

For runnable examples check out the [demo](https://github.com/arched-dev/flarchitect/tree/master/demo) directory, browse the [unit tests](https://github.com/arched-dev/flarchitect/tree/master/tests) for real-world usage patterns or read the [full documentation](docs/source/index.rst).
