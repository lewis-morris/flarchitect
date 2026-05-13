"""Helpers for deriving consistent cookie settings."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from flask import current_app, has_app_context

from flarchitect.utils.config_helpers import get_config_or_model_meta

# Mapping of Flask session cookie config keys to ``set_cookie`` kwargs.
_SESSION_CONFIG_KEY_MAP: dict[str, str] = {
    "SESSION_COOKIE_DOMAIN": "domain",
    "SESSION_COOKIE_PATH": "path",
    "SESSION_COOKIE_SECURE": "secure",
    "SESSION_COOKIE_HTTPONLY": "httponly",
    "SESSION_COOKIE_SAMESITE": "samesite",
    "SESSION_COOKIE_PARTITIONED": "partitioned",
}


def cookie_settings(
    overrides: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Return cookie keyword arguments aligned with project configuration.

    The helper combines the optional ``API_COOKIE_DEFAULTS`` configuration with
    Flask's session cookie settings (``SESSION_COOKIE_*``) so custom blueprints
    and background tasks can apply a consistent security posture without
    duplicating configuration lookups. Callers may supply ``overrides`` or
    ``**kwargs`` to adjust individual attributes for a specific cookie.

    Args:
        overrides: Mapping of cookie keyword arguments to merge into the
            defaults.
        **kwargs: Additional keyword arguments overriding both configured
            defaults and ``overrides``.

    Returns:
        dict[str, Any]: Keyword arguments suitable for ``Response.set_cookie``.
    """

    settings: dict[str, Any] = {}

    if has_app_context():
        configured_defaults = get_config_or_model_meta("API_COOKIE_DEFAULTS", default=None)
        if isinstance(configured_defaults, Mapping):
            settings.update(configured_defaults)

        app = current_app._get_current_object()
        for config_key, target in _SESSION_CONFIG_KEY_MAP.items():
            if target not in settings:
                value = app.config.get(config_key)
                if value is not None:
                    settings[target] = value

        if "max_age" not in settings:
            max_age = app.config.get("SESSION_COOKIE_MAX_AGE")
            if max_age is not None:
                settings["max_age"] = max_age
    elif overrides is None and not kwargs:
        # No application context and no explicit overrides; return empty mapping.
        pass
    else:
        configured_defaults = None

    if overrides:
        settings.update(dict(overrides))

    if kwargs:
        settings.update(kwargs)

    return settings


__all__ = ["cookie_settings"]
