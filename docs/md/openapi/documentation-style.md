[← Back to API Documentation index](index.md)

# Documentation style
By default, flarchitect renders docs with Redoc. To switch to Swagger UI set
API_DOCS_STYLE <configuration.html#DOCS_STYLE> = "swagger" in your Flask configuration. The only accepted
values are `"redoc"` and `"swagger"`. Redoc provides a clean read-only
reference, while Swagger UI adds an interactive "try it out" console:
```
app.config["API_DOCS_STYLE"] = "swagger"
```
The documentation itself is hosted at API_DOCUMENTATION_URL <configuration.html#DOCUMENTATION_URL> (default
`/docs`).

