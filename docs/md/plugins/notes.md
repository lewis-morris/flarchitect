[← Back to Plugins index](index.md)

# Notes
- Plugins are additive: multiple plugins can be installed; they are called in order.
- Returning `None` means "no change". Where supported, the first non-`None` return
    value wins (e.g., response replacement).
- Existing callback config keys (e.g., `API_SETUP_CALLBACK`) continue to work and
    compose with plugins.

