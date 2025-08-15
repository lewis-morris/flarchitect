"""JWT error handling tests."""

from __future__ import annotations

import datetime
from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import Mock

import jwt
import pytest
from flask import Flask
from pytest import MonkeyPatch

from flarchitect.authentication.jwt import decode_token, refresh_access_token
from flarchitect.exceptions import CustomHTTPException


@pytest.fixture()
def app_ctx() -> Generator[Flask, None, None]:
    """Provide a Flask application context for JWT operations."""
    app = Flask(__name__)
    with app.app_context():
        yield app


@pytest.fixture()
def secret_key() -> str:
    """Return the secret key used for encoding test JWTs."""
    return "secret"


@pytest.fixture()
def refresh_secret() -> str:
    """Return the secret key for refresh token encoding."""
    return "refresh"


@pytest.fixture()
def expired_token(secret_key: str) -> str:
    """Create an expired JWT for testing."""
    payload = {
        "sub": "user",
        "iat": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=2),
        "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


@pytest.fixture()
def malformed_token() -> str:
    """Return a malformed JWT string."""
    return "invalid.token"


@pytest.fixture()
def valid_refresh_token(refresh_secret: str) -> str:
    """Generate a valid refresh token for testing."""
    payload = {
        "sub": "user",
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30),
    }
    return jwt.encode(payload, refresh_secret, algorithm="HS256")


def test_decode_token_expired(app_ctx: Flask, expired_token: str, secret_key: str) -> None:
    """Ensure ``decode_token`` raises ``CustomHTTPException`` for expired tokens."""
    with pytest.raises(CustomHTTPException) as exc_info:
        decode_token(expired_token, secret_key)
    assert exc_info.value.status_code == 401
    assert exc_info.value.reason == "Token has expired"


def test_decode_token_malformed(app_ctx: Flask, malformed_token: str, secret_key: str) -> None:
    """Ensure ``decode_token`` raises ``CustomHTTPException`` for malformed tokens."""
    with pytest.raises(CustomHTTPException) as exc_info:
        decode_token(malformed_token, secret_key)
    assert exc_info.value.status_code == 401
    assert exc_info.value.reason == "Invalid token"


def test_refresh_access_token_deletes_expired_token(
    app_ctx: Flask,
    valid_refresh_token: str,
    refresh_secret: str,
    monkeypatch: MonkeyPatch,
) -> None:
    """Verify expired refresh tokens are deleted and return ``403``."""
    app_ctx.config["REFRESH_SECRET_KEY"] = refresh_secret

    past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    stored = SimpleNamespace(expires_at=past_time, user_lookup="user", user_pk="1")

    delete_mock = Mock()
    monkeypatch.setattr("flarchitect.authentication.jwt.delete_refresh_token", delete_mock)
    monkeypatch.setattr("flarchitect.authentication.jwt.get_refresh_token", lambda token: stored)

    with pytest.raises(CustomHTTPException) as exc_info:
        refresh_access_token(valid_refresh_token)

    assert exc_info.value.status_code == 403
    assert exc_info.value.reason == "Invalid or expired refresh token"
    delete_mock.assert_called_once_with(valid_refresh_token)


def test_refresh_access_token_missing_secret_key(app_ctx: Flask, valid_refresh_token: str, monkeypatch: MonkeyPatch) -> None:
    """Ensure a ``500`` is raised when ``REFRESH_SECRET_KEY`` is missing."""
    monkeypatch.delenv("REFRESH_SECRET_KEY", raising=False)
    app_ctx.config.pop("REFRESH_SECRET_KEY", None)

    get_mock = Mock()
    delete_mock = Mock()
    monkeypatch.setattr("flarchitect.authentication.jwt.get_refresh_token", get_mock)
    monkeypatch.setattr("flarchitect.authentication.jwt.delete_refresh_token", delete_mock)

    with pytest.raises(CustomHTTPException) as exc_info:
        refresh_access_token(valid_refresh_token)

    assert exc_info.value.status_code == 500
    assert exc_info.value.reason == "REFRESH_SECRET_KEY missing"
    get_mock.assert_not_called()
    delete_mock.assert_not_called()
