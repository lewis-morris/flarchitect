[← Back to WebSockets index](index.md)

# Enable The Endpoint
1. Install the optional dependency:
    pip install flask-sock
2. Enable WebSockets in your Flask config and (optionally) set the path:
```
class Config:
    API_ENABLE_WEBSOCKETS = True
    API_WEBSOCKET_PATH = "/ws"  # optional, defaults to "/ws"
```
1. Initialise flarchitect as usual. If `flask_sock` is present, the
    `/ws` route is registered automatically:
```
app = Flask(__name__)
architect = Architect(app)

# no extra steps required
```

