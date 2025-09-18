[← Back to Advanced Configuration index](index.md)

# CORS
To enable Cross-Origin Resource Sharing (CORS) <[https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)>
for your API, set API_ENABLE_CORS <configuration.html#ENABLE_CORS> to `True` in the application
configuration. When active, CORS headers are applied to matching routes
defined in `CORS_RESOURCES`.
`CORS_RESOURCES` accepts a mapping of URL patterns to their respective
options, mirroring the format used by Flask-CORS <[https://flask-cors.readthedocs.io/](https://flask-cors.readthedocs.io/)>.
```
class Config:
    API_ENABLE_CORS = True
    CORS_RESOURCES = {
        r"/api/*": {"origins": "*"}
    }
```
If `flask-cors` is installed, these settings are passed through to that
extension. Without it, `flarchitect` compiles the patterns in
`CORS_RESOURCES` and adds an `Access-Control-Allow-Origin` header for
matching requests. Only origin checking is performed; other CORS headers are
left untouched.
`flask-cors`-free minimal configuration:
```
class Config:
    API_ENABLE_CORS = True
    CORS_RESOURCES = {r"/api/*": {"origins": ["https://example.com"]}}
```

## Example
The following snippet enables CORS for all API routes:
```
from flask import Flask
from flarchitect import Architect

app = Flask(__name__)
app.config["API_ENABLE_CORS"] = True
app.config["CORS_RESOURCES"] = {r"/api/*": {"origins": "*"}}

architect = Architect(app)

if __name__ == "__main__":
    app.run()
```
See the configuration <configuration> page for the full list of
available CORS settings.

