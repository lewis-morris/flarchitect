"""Tests for secret key fallback order in ``get_user_from_token``."""

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from flarchitect.authentication.jwt import generate_access_token, get_user_from_token
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


class StrictInteger(TypeDecorator):
    """Integer column that rejects non-int bind parameters."""

    impl = Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):  # type: ignore[override]
        if value is None:
            return None
        if not isinstance(value, int):
            raise TypeError("StrictInteger columns require int values")
        return value


@pytest.fixture()
def client_jwt_integer_lookup():
    """Test client whose lookup and primary key columns are integer-backed."""

    db = SQLAlchemy()

    class NumericUser(db.Model):  # type: ignore[too-many-ancestors]
        __tablename__ = "numeric_lookup_users"

        id = db.Column(StrictInteger, primary_key=True)
        username = db.Column(StrictInteger, unique=True)
        password_hash = db.Column(db.String)
        api_key_hash = db.Column(db.String)

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": StaticPool},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_AUTHENTICATE_METHOD=["jwt"],
        API_CREATE_DOCS=False,
        API_USER_MODEL=NumericUser,
        API_USER_LOOKUP_FIELD="username",
    )
    app.config["ACCESS_SECRET_KEY"] = "access"

    db.init_app(app)

    with app.app_context():
        db.create_all()
        user = NumericUser(username=101, password_hash="unused", api_key_hash="unused")
        db.session.add(user)
        db.session.commit()

        access_token = generate_access_token(user)

        yield app.test_client(), access_token, user

        db.session.remove()


def test_integer_lookup_payloads_coerced(client_jwt_integer_lookup):
    """String payload values are coerced to ``int`` for integer-backed fields."""

    client, access_token, seeded_user = client_jwt_integer_lookup

    with client.application.app_context():
        user = get_user_from_token(access_token)

    assert user.username == seeded_user.username
    assert isinstance(user.username, int)
