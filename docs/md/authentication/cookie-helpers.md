[← Back to Authentication index](index.md)

# Cookie helpers
`flarchitect.authentication.helpers.load_user_from_cookie` bridges cookie-based sessions to
`current_user` for bespoke middleware or blueprints. It reads the configured cookie, validates the
token and calls `set_current_user`. The helper returns `True` when a user was attached
successfully. Pair it with flarchitect.utils.cookie_settings, which merges the optional
`API_COOKIE_DEFAULTS` mapping with Flask's `SESSION_COOKIE_*` configuration to produce
keyword arguments for `Response.set_cookie`.

