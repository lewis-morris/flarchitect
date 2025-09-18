[← Back to Configuration index](index.md)

# Core configuration
Some settings are essential for initialising the extension and controlling its
automatic behaviour.
At a minimum, provide a title and version for your API:
```
class Config:
    API_TITLE = "My API"
    API_VERSION = "1.0"
```
Two additional flags, `FULL_AUTO` and `AUTO_NAME_ENDPOINTS`, toggle the
automatic registration of routes and the generation of default endpoint
summaries. Both default to `True` and may be disabled when you need manual
control.
```
class Config:
    FULL_AUTO = False           # register routes manually
    AUTO_NAME_ENDPOINTS = False # keep custom summaries
```

