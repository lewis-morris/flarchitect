[← Back to Advanced Configuration index](index.md)

# Initialising with optional features
`Architect.init_app` accepts keyword arguments that toggle optional
behaviour like caching, CORS handling and automatic documentation
generation.
```
from flarchitect import Architect

architect = Architect()
architect.init_app(
    app,
    cache={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300},
    enable_cors=True,
    create_docs=True,
)
```
These keywords mirror their respective `API_*` configuration values and
allow feature flags to be set programmatically during initialisation.
As traffic increases, managing how often clients can hit your API becomes
critical.

