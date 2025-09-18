# Config by Method Models

> Global < Model < **Model Method**
Model Method
These values are defined as Meta class attributes in your SQLAlchemy models and configure specific behaviour per
HTTP method for a specific model.
- They should always be lowercase
- They should always omit any `API_` prefix.
- They should be prefixed with the HTTP method you want to configure, e.g. `get_`, `post_`, `patch_`, `delete_`
Values defined here will apply per model/HTTP method and cannot be overridden.

## Sections

- [Example](example.md)
