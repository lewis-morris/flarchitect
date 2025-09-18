[← Back to API Documentation index](index.md)

# Automatic generation
When API_CREATE_DOCS <configuration.html#CREATE_DOCS> is enabled (it is `True` by default) the
specification is built on start-up by inspecting the routes and schemas
registered with flarchitect.Architect.  Any models
added later are included the next time the application boots.

