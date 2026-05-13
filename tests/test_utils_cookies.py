"""Tests for cookie helper utilities."""

from flask import Flask

from flarchitect.utils.cookies import cookie_settings


def _make_app(**config):
    app = Flask(__name__)
    app.config.update(TESTING=True)
    app.config.update(config)
    return app


def test_cookie_settings_uses_api_defaults():
    app = _make_app(API_COOKIE_DEFAULTS={"secure": True, "httponly": True, "samesite": "Strict"})

    with app.app_context():
        result = cookie_settings()

    assert result["secure"] is True
    assert result["httponly"] is True
    assert result["samesite"] == "Strict"


def test_cookie_settings_merges_session_config():
    app = _make_app(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_MAX_AGE=3600,
    )

    with app.app_context():
        result = cookie_settings()

    assert result["secure"] is True
    assert result["httponly"] is True
    assert result["samesite"] == "Lax"
    assert result["max_age"] == 3600


def test_cookie_settings_supports_overrides():
    app = _make_app(API_COOKIE_DEFAULTS={"secure": True, "httponly": True, "path": "/"})

    with app.app_context():
        result = cookie_settings({"httponly": False}, secure=False, domain="example.com")

    assert result["secure"] is False  # kwargs override config/defaults
    assert result["httponly"] is False  # mapping override applied
    assert result["path"] == "/"
    assert result["domain"] == "example.com"


def test_cookie_settings_outside_app_context_returns_overrides_only():
    result = cookie_settings(secure=True)
    assert result == {"secure": True}
