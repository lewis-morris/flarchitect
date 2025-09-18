[← Back to FAQ index](index.md)

# Troubleshooting
Ensure API_CREATE_DOCS <configuration.html#CREATE_DOCS> is set to `True` and that the
flarchitect.Architect has been initialised. If
you mount the app under a prefix, check `documentation_url_prefix`.
Confirm the model has a `Meta` class and the endpoint isn't blocked by
API_BLOCK_METHODS <configuration.html#BLOCK_METHODS>. Rebuilding the application will refresh the
specification.

