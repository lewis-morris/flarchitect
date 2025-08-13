"""Unit tests for :class:`Architect` helper methods."""

from types import SimpleNamespace

import pytest
from flask import Flask
from marshmallow import Schema

from flarchitect import Architect
from flarchitect.exceptions import CustomHTTPException


class DummySchema(Schema):
    """Placeholder schema for decorator tests."""


def create_app(**config) -> Flask:
    app = Flask(__name__)
    app.config.update(
        FULL_AUTO=False,
        API_CREATE_DOCS=False,
        API_RATE_LIMIT_STORAGE_URI="memory://",
        **config,
    )
    return app


def test_handle_auth_custom(monkeypatch):
    """Verify ``_handle_auth`` respects custom authentication."""

    app = create_app(API_AUTHENTICATE_METHOD=["custom"], API_CUSTOM_AUTH=lambda: True)
    with app.app_context():
        architect = Architect(app=app)
    with app.test_request_context("/"):
        architect._handle_auth(model=None, output_schema=None, input_schema=None, auth_flag=True)

    app.config["API_CUSTOM_AUTH"] = lambda: False
    with app.test_request_context("/"), pytest.raises(CustomHTTPException):
        architect._handle_auth(model=None, output_schema=None, input_schema=None, auth_flag=True)


def test_apply_schemas_uses_handle_one(monkeypatch):
    """``_apply_schemas`` should delegate to ``handle_one`` when ``many`` is ``False``."""

    app = create_app()
    with app.app_context():
        architect = Architect(app=app)
    called = {"one": False, "many": False}

    def fake_handle_one(*_args, **_kwargs):  # type: ignore[unused-ignore]
        called["one"] = True

        def decorator(f):
            return f

        return decorator

    def fake_handle_many(*_args, **_kwargs):  # type: ignore[unused-ignore]
        called["many"] = True

        def decorator(f):
            return f

        return decorator

    monkeypatch.setattr("flarchitect.core.architect.handle_one", fake_handle_one)
    monkeypatch.setattr("flarchitect.core.architect.handle_many", fake_handle_many)

    def dummy():
        return "ok"

    architect._apply_schemas(dummy, DummySchema, None, many=False)
    assert called["one"] and not called["many"]


def test_apply_schemas_uses_handle_many(monkeypatch):
    """``_apply_schemas`` should delegate to ``handle_many`` when ``many`` is ``True``."""

    app = create_app()
    with app.app_context():
        architect = Architect(app=app)
    called = {"one": False, "many": False}

    def fake_handle_one(*_args, **_kwargs):  # type: ignore[unused-ignore]
        called["one"] = True

        def decorator(f):
            return f

        return decorator

    def fake_handle_many(*_args, **_kwargs):  # type: ignore[unused-ignore]
        called["many"] = True

        def decorator(f):
            return f

        return decorator

    monkeypatch.setattr("flarchitect.core.architect.handle_one", fake_handle_one)
    monkeypatch.setattr("flarchitect.core.architect.handle_many", fake_handle_many)

    def dummy():
        return "ok"

    architect._apply_schemas(dummy, DummySchema, None, many=True)
    assert called["many"] and not called["one"]


def test_apply_rate_limit_valid(monkeypatch):
    """A valid rate limit string should invoke the limiter with the value."""

    app = create_app(API_RATE_LIMIT="1 per minute")
    recorded = {}

    def fake_limit(rate):
        recorded["rate"] = rate

        def decorator(f):
            return f

        return decorator

    with app.app_context():
        architect = Architect(app=app)
        architect.limiter.limit = fake_limit  # type: ignore[method-assign]

        def dummy():
            return "ok"

        architect._apply_rate_limit(dummy, model=None, output_schema=None, input_schema=None)

    assert recorded["rate"] == "1 per minute"


def test_apply_rate_limit_invalid_logs(monkeypatch):
    """An invalid rate limit should log an error and return the original function."""

    app = create_app(API_RATE_LIMIT="invalid")
    with app.app_context():
        architect = Architect(app=app)

    monkeypatch.setattr(
        "flarchitect.core.architect.validate_flask_limiter_rate_limit_string",
        lambda _s: False,
    )

    monkeypatch.setattr(
        "flarchitect.core.architect.find_rule_by_function",
        lambda _self, _f: SimpleNamespace(rule="/dummy"),
    )

    messages = {}

    def fake_error(msg):
        messages["msg"] = msg

    monkeypatch.setattr("flarchitect.core.architect.logger.error", fake_error)

    def dummy():
        return "ok"

    with app.app_context():
        result = architect._apply_rate_limit(dummy, model=None, output_schema=None, input_schema=None)

    assert messages["msg"].startswith("Rate limit definition not a string")
    assert result is dummy
