"""Tests for refresh token rotation, revocation (deny-list), and auditing."""

from __future__ import annotations

import datetime
from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import StaticPool

from flarchitect import Architect
from flarchitect.authentication.token_store import RefreshToken, get_session


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)

    def check_password(self, password: str) -> bool:  # pragma: no cover - simple helper
        return self.password == password


@pytest.fixture()
def client_jwt_app() -> Generator[FlaskClient, None, None]:
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": StaticPool},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FULL_AUTO=False,
        API_CREATE_DOCS=False,
        API_RATE_LIMIT_STORAGE_URI="memory://",
        API_AUTHENTICATE_METHOD=["jwt"],
        API_USER_MODEL=User,
        API_USER_LOOKUP_FIELD="username",
        API_CREDENTIAL_CHECK_METHOD="check_password",
    )
    app.config["ACCESS_SECRET_KEY"] = "access"
    app.config["REFRESH_SECRET_KEY"] = "refresh"
    db.init_app(app)

    with app.app_context():
        architect = Architect(app=app)
        architect.init_api(app=app, api_full_auto=False)
        architect.api.make_auth_routes()

        db.create_all()
        user = User(username="eve", password="secret")
        db.session.add(user)
        db.session.commit()

        yield app.test_client()


def test_refresh_rotation_marks_old_revoked_and_links_new(client_jwt_app: FlaskClient) -> None:
    # Login to obtain tokens
    resp = client_jwt_app.post("/auth/login", json={"username": "eve", "password": "secret"})
    assert resp.status_code == 200
    data = resp.get_json()["value"]
    old_refresh = data["refresh_token"]

    # Refresh to rotate
    resp2 = client_jwt_app.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert resp2.status_code == 200
    data2 = resp2.get_json()["value"]
    new_refresh = data2["refresh_token"]

    # Old token should be revoked and linked to new token, with last_used_at set
    with get_session(RefreshToken) as session:
        row = session.get(RefreshToken, old_refresh)
        assert row is not None
        assert row.revoked is True
        assert row.replaced_by == new_refresh
        assert row.last_used_at is not None

    # Using the old refresh again should fail (hidden by get_refresh_token logic and route validation)
    resp3 = client_jwt_app.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert resp3.status_code in (401, 403)


def test_revoke_refresh_token_blocks_use(client_jwt_app: FlaskClient) -> None:
    # Login to obtain tokens
    resp = client_jwt_app.post("/auth/login", json={"username": "eve", "password": "secret"})
    assert resp.status_code == 200
    data = resp.get_json()["value"]
    refresh = data["refresh_token"]

    # Manually mark as revoked to simulate admin action
    from flarchitect.authentication.token_store import revoke_refresh_token

    revoke_refresh_token(refresh)

    # Attempting to use should fail
    resp2 = client_jwt_app.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp2.status_code in (401, 403)
