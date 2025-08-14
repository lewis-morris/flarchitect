"""Tests for secret key fallback order in ``get_user_from_token``."""

import pytest

from flarchitect.authentication.jwt import get_user_from_token
from flarchitect.exceptions import CustomHTTPException

pytest_plugins = ["tests.test_authentication"]


def test_secret_key_argument_overrides_environment(monkeypatch, client_jwt):
    """Explicit secret key should take precedence over environment and config values."""
    client, access_token, _ = client_jwt
    monkeypatch.setenv("ACCESS_SECRET_KEY", "wrong")
    client.application.config["ACCESS_SECRET_KEY"] = "also_wrong"
    with client.application.app_context():
        user = get_user_from_token(access_token, secret_key="access")
        assert user.username == "carol"


def test_environment_fallback_used_when_no_argument(monkeypatch, client_jwt):
    """Environment variable is used when no key is passed explicitly."""
    client, access_token, _ = client_jwt
    monkeypatch.setenv("ACCESS_SECRET_KEY", "access")
    client.application.config["ACCESS_SECRET_KEY"] = "wrong"
    with client.application.app_context():
        user = get_user_from_token(access_token)
        assert user.username == "carol"


def test_config_fallback_used_last(monkeypatch, client_jwt):
    """App config value is used when neither argument nor environment variable is set."""
    client, access_token, _ = client_jwt
    monkeypatch.delenv("ACCESS_SECRET_KEY", raising=False)
    client.application.config["ACCESS_SECRET_KEY"] = "access"
    with client.application.app_context():
        user = get_user_from_token(access_token)
        assert user.username == "carol"


def test_access_secret_key_missing(monkeypatch, client_jwt):
    """Raise ``CustomHTTPException`` when ``ACCESS_SECRET_KEY`` is absent."""

    client, access_token, _ = client_jwt
    monkeypatch.delenv("ACCESS_SECRET_KEY", raising=False)
    client.application.config.pop("ACCESS_SECRET_KEY", None)

    with (
        client.application.app_context(),
        pytest.raises(CustomHTTPException) as exc_info,
    ):
        get_user_from_token(access_token)

    assert exc_info.value.status_code == 500
    assert exc_info.value.reason == "ACCESS_SECRET_KEY missing"
