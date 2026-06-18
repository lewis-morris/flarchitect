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


def _configured_cookie_defaults() -> dict[str, Any]:
    configured_defaults = get_config_or_model_meta("API_COOKIE_DEFAULTS", default=None)
    if isinstance(configured_defaults, Mapping):
        return dict(configured_defaults)
    return {}


def _session_cookie_settings(settings: Mapping[str, Any]) -> dict[str, Any]:
    app = current_app._get_current_object()
    session_settings: dict[str, Any] = {}

    for config_key, target in _SESSION_CONFIG_KEY_MAP.items():
        if target in settings:
            continue
        value = app.config.get(config_key)
        if value is not None:
            session_settings[target] = value

    if "max_age" not in settings:
        max_age = app.config.get("SESSION_COOKIE_MAX_AGE")
        if max_age is not None:
            session_settings["max_age"] = max_age

    return session_settings


def _app_cookie_settings() -> dict[str, Any]:
    settings = _configured_cookie_defaults()
    settings.update(_session_cookie_settings(settings))
    return settings


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

    settings = _app_cookie_settings() if has_app_context() else {}

    if overrides:
        settings.update(dict(overrides))

    if kwargs:
        settings.update(kwargs)

    return settings


__all__ = ["cookie_settings"]
