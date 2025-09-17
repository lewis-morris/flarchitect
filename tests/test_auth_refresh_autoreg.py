"""Auto-registration tests for the JWT refresh route."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import StaticPool

from flarchitect import Architect
from flarchitect.authentication.jwt import generate_refresh_token


db = SQLAlchemy()


class User(db.Model):  # type: ignore[misc]
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)

    def check_password(self, password: str) -> bool:  # pragma: no cover - helper
        return self.password == password


def _base_app_config() -> dict:
    return dict(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": StaticPool},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FULL_AUTO=False,
        API_CREATE_DOCS=False,
        API_USER_MODEL=User,
        API_USER_LOOKUP_FIELD="username",
        API_CREDENTIAL_CHECK_METHOD="check_password",
    )


@pytest.fixture()
def client_app() -> Generator[FlaskClient, None, None]:
    app = Flask(__name__)
    cfg = _base_app_config()
    cfg["API_AUTHENTICATE_METHOD"] = ["jwt"]
    app.config.update(cfg)
    app.config["ACCESS_SECRET_KEY"] = "access"
    app.config["REFRESH_SECRET_KEY"] = "refresh"
    db.init_app(app)

    with app.app_context():
        architect = Architect(app=app)
        architect.init_api(app=app, api_full_auto=False)
        architect.api.make_auth_routes()

        db.create_all()
        user = User(username="dave", password="p@ss")
        db.session.add(user)
        db.session.commit()

        # create refresh token in store for the user
        refresh = generate_refresh_token(user)

        client = app.test_client()
        # Expose helper on client for tests
        client._refresh_token = refresh  # type: ignore[attr-defined]
        yield client


def test_refresh_success_and_missing_and_invalid(client_app: FlaskClient) -> None:
    # success
    resp = client_app.post("/auth/refresh", json={"refresh_token": client_app._refresh_token})  # type: ignore[attr-defined]
    assert resp.status_code == 200
    body = resp.get_json()
    assert isinstance(body, dict) and isinstance(body.get("value"), dict)
    assert "access_token" in body["value"]

    # missing token
    resp2 = client_app.post("/auth/refresh", json={})
    assert resp2.status_code == 400

    # clearly invalid token
    resp3 = client_app.post("/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert resp3.status_code in (401, 403)


def test_auto_auth_routes_toggle_disables_refresh() -> None:
    app = Flask(__name__)
    cfg = _base_app_config()
    cfg.update(API_AUTHENTICATE_METHOD=["jwt"], API_AUTO_AUTH_ROUTES=False)
    app.config.update(cfg)
    app.config["ACCESS_SECRET_KEY"] = "access"
    app.config["REFRESH_SECRET_KEY"] = "refresh"
    db.init_app(app)

    with app.app_context():
        architect = Architect(app=app)
        architect.init_api(app=app, api_full_auto=False)
        architect.api.make_auth_routes()
        client = app.test_client()

        # Route should not exist
        res = client.post("/auth/refresh", json={"refresh_token": "x"})
        assert res.status_code == 404


def test_refresh_not_registered_when_jwt_not_enabled() -> None:
    app = Flask(__name__)
    cfg = _base_app_config()
    cfg["API_AUTHENTICATE_METHOD"] = ["basic"]
    app.config.update(cfg)
    db.init_app(app)

    with app.app_context():
        architect = Architect(app=app)
        architect.init_api(app=app, api_full_auto=False)
        architect.api.make_auth_routes()
        client = app.test_client()

        res = client.post("/auth/refresh", json={"refresh_token": "x"})
        assert res.status_code == 404


def test_configurable_refresh_path() -> None:
    app = Flask(__name__)
    cfg = _base_app_config()
    cfg.update(API_AUTHENTICATE_METHOD=["jwt"], API_AUTH_REFRESH_ROUTE="/auth/reissue")
    app.config.update(cfg)
    app.config["ACCESS_SECRET_KEY"] = "access"
    app.config["REFRESH_SECRET_KEY"] = "refresh"
    db.init_app(app)

    with app.app_context():
        architect = Architect(app=app)
        architect.init_api(app=app, api_full_auto=False)
        architect.api.make_auth_routes()

        db.create_all()
        user = User(username="erin", password="pw")
        db.session.add(user)
        db.session.commit()

        refresh = generate_refresh_token(user)

        client = app.test_client()
        # New path works
        ok = client.post("/auth/reissue", json={"refresh_token": refresh})
        assert ok.status_code == 200
        # Default path absent
        missing = client.post("/auth/refresh", json={"refresh_token": refresh})
        assert missing.status_code == 404

