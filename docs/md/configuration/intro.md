[← Back to Configuration index](index.md)

# Intro
In flarchitect, configuration options are essential for customising the API and its accompanying documentation.
These settings can be provided through `Flask`_ config values or directly within `SQLAlchemy`_ model classes using `Meta` classes.
Beyond the basics, the extension supports hooks and advanced flags for post-serialisation callbacks, rate limiting, field exclusion, blueprint naming, endpoint naming via API_ENDPOINT_NAMER, soft deletion, and per-method documentation summaries.
`Flask`_ config values offer a straightforward, standardised way to modify the extension's behaviour at a global or model level.

