[← Back to Quick Start index](index.md)

# Configure Flask
Register the extension with a Flask app and supply configuration values.
```
from flask import Flask
from flarchitect import Architect

app = Flask(__name__)

app.config["API_TITLE"] = "My API"
app.config["API_VERSION"] = "1.0"
app.config["API_BASE_MODEL"] = db.Model

architect = Architect(app)
```
These settings tell **flarchitect** how to build the API and where to find your models.

