"""Tests for refresh token persistence logic."""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from flarchitect.authentication.jwt import generate_refresh_token, refresh_access_token
from flarchitect.authentication.token_store import get_refresh_token
from flarchitect.exceptions import CustomHTTPException
from tests.test_authentication import User
from tests.test_authentication import client_jwt as client_jwt_fixture

client_jwt = client_jwt_fixture


def test_refresh_token_stored(client_jwt: tuple[FlaskClient, str, str]) -> None:
    """Generated refresh tokens are persisted."""
    client, _, refresh_token = client_jwt
    app: Flask = client.application
    with app.app_context():
        stored = get_refresh_token(refresh_token)
        assert stored is not None
        assert stored.user_lookup == "carol"


def test_refresh_access_token_deletes_token(
    client_jwt: tuple[FlaskClient, str, str],
) -> None:
    """Using a refresh token removes it from the store."""
    client, _, refresh_token = client_jwt
    app: Flask = client.application
    with app.app_context():
        assert get_refresh_token(refresh_token) is not None
        refresh_access_token(refresh_token)
        assert get_refresh_token(refresh_token) is None


def test_expired_refresh_token_deleted(
    client_jwt: tuple[FlaskClient, str, str],
) -> None:
    """Expired refresh tokens are purged when used."""
    client, _, _ = client_jwt
    app: Flask = client.application
    with app.app_context():
        user = User.query.filter_by(username="carol").one()
        expired_refresh = generate_refresh_token(user, expires_in_minutes=-1)
        assert get_refresh_token(expired_refresh) is not None
        with pytest.raises(CustomHTTPException):
            refresh_access_token(expired_refresh)
        assert get_refresh_token(expired_refresh) is None
