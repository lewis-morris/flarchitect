[← Back to Manual Routes index](index.md)

# Basic usage
```
from flask import Flask
from marshmallow import Schema, fields
from flarchitect import Architect

app = Flask(__name__)
app.config.update(
    API_TITLE="My API",
    API_VERSION="1.0",
    # Enable JWT (or your chosen method) if you want auth enforced
    API_AUTHENTICATE_METHOD=["jwt"],
)

architect = Architect(app)

class HelloOut(Schema):
    message = fields.String(required=True)

@app.get("/hello")
@architect.schema_constructor(
    output_schema=HelloOut,   # serialise the return value with this schema
    group_tag="Custom",       # group in docs
    auth=True,                # enforce configured auth on this route
)
def hello():
    return {"message": "world"}
```
The decorator automatically:
- Validates/serialises using the provided schemas.
- Enforces authentication (unless `auth=False` is set).
- Applies any configured rate limit (see `API_RATE_LIMIT` and model/method overrides).
- Registers the route so it appears in the OpenAPI spec and docs.

