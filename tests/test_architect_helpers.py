"""Unit tests for :class:`Architect` helper methods."""

import pytest
from flask import Flask
from flask_limiter.errors import RateLimitExceeded
from marshmallow import Schema, fields

from flarchitect import Architect
from flarchitect.exceptions import CustomHTTPException
from flarchitect.logging import logger


class DummySchema(Schema):
    """Simple schema with a single ``name`` field."""

    name = fields.String(required=True)


def create_app(**config) -> Flask:
    app = Flask(__name__)
    app.config.update(
        FULL_AUTO=False,
        API_CREATE_DOCS=False,
        API_RATE_LIMIT_STORAGE_URI="memory://",
        **config,
    )
    return app


def test_handle_auth_custom() -> None:
    """Verify ``_handle_auth`` respects custom authentication."""

    app = create_app(API_AUTHENTICATE_METHOD=["custom"], API_CUSTOM_AUTH=lambda: True)
    with app.app_context():
        architect = Architect(app=app)
    with app.test_request_context("/"):
        architect._handle_auth(
            model=None, output_schema=None, input_schema=None, auth_flag=True
        )

    app.config["API_CUSTOM_AUTH"] = lambda: False
    with app.test_request_context("/"), pytest.raises(CustomHTTPException):
        architect._handle_auth(
            model=None, output_schema=None, input_schema=None, auth_flag=True
        )


def test_apply_schemas_uses_handle_one() -> None:
    """``_apply_schemas`` should use ``handle_one`` for single objects."""

    app = create_app()
    with app.app_context():
        architect = Architect(app=app)

    def dummy() -> dict[str, str]:
        return {"name": "Alice"}

    with app.test_request_context("/"):
        wrapped = architect._apply_schemas(dummy, DummySchema, None, many=False)
        result = wrapped()
    assert result.get_json()["value"] == {"name": "Alice"}


def test_apply_schemas_uses_handle_many() -> None:
    """``_apply_schemas`` should use ``handle_many`` for lists."""

    app = create_app()
    with app.app_context():
        architect = Architect(app=app)

    def dummy() -> list[dict[str, str]]:
        return [{"name": "Alice"}]

    with app.test_request_context("/"):
        wrapped = architect._apply_schemas(dummy, DummySchema, None, many=True)
        result = wrapped()
    assert result.get_json()["value"] == [{"name": "Alice"}]


def test_apply_rate_limit_valid() -> None:
    """A valid rate limit string should enforce limits."""

    app = create_app(API_RATE_LIMIT="1 per minute")
    with app.app_context():
        architect = Architect(app=app)

        @app.route("/limited")
        def dummy() -> str:
            return "ok"

        wrapped = architect._apply_rate_limit(
            dummy, model=None, output_schema=None, input_schema=None
        )

        with app.test_request_context("/limited"):
            assert wrapped() == "ok"
        with app.test_request_context("/limited"), pytest.raises(RateLimitExceeded):
            wrapped()


def test_apply_rate_limit_invalid_logs(capsys: pytest.CaptureFixture[str]) -> None:
    """An invalid rate limit should log an error and return the original function."""

    app = create_app(API_RATE_LIMIT="invalid")
    with app.app_context():
        architect = Architect(app=app)

        @app.route("/dummy")
        def dummy() -> str:  # pragma: no cover - minimal route
            return "ok"

        logger.verbosity_level = 1
        result = architect._apply_rate_limit(
            dummy, model=None, output_schema=None, input_schema=None
        )
        output = capsys.readouterr().out

        assert "Rate limit definition not a string" in output
        assert result is dummy
