"""Integration tests for demo authentication strategies."""

from __future__ import annotations

import base64
from collections.abc import Callable

from flask.testing import FlaskClient
from marshmallow import Schema, fields

from demo.authentication.app_base import BaseConfig, User, create_app, db, schema
from flarchitect.authentication.user import get_current_user, set_current_user


class ProfileSchema(Schema):
    """Minimal schema exposing the authenticated user's username."""

    username = fields.String(required=True)


def _prepare_app(config: type[BaseConfig], setup: Callable[[FlaskClient], None]) -> FlaskClient:
    """Create an app using ``config`` and seed a user via ``setup``."""

    app = create_app(config)

    @app.get("/profile")
    @schema.schema_constructor(output_schema=ProfileSchema, auth=True)
    def profile() -> dict[str, str]:
        """Return the authenticated user's profile."""

        user = get_current_user()
        return {"username": user.username}

    client = app.test_client()
    with app.app_context():
        db.drop_all()
        db.create_all()
        setup(client)
    return client


def test_jwt_demo_login_and_profile() -> None:
    """JWT tokens grant access to the protected profile endpoint."""

    class JWTConfig(BaseConfig):
        API_AUTHENTICATE_METHOD = ["jwt"]
        ACCESS_SECRET_KEY = "access-secret"
        REFRESH_SECRET_KEY = "refresh-secret"
        API_USER_MODEL = User
        API_USER_LOOKUP_FIELD = "username"
        API_CREDENTIAL_CHECK_METHOD = "check_password"

    def seed(_: FlaskClient) -> None:
        user = User(username="alice", password="wonderland")
        db.session.add(user)
        db.session.commit()

    client = _prepare_app(JWTConfig, seed)
    resp = client.post(
        "/auth/login",
        json={"username": "alice", "password": "wonderland"},
    )
    assert resp.status_code == 200
    tokens = resp.get_json()["value"]

    profile = client.get(
        "/profile",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert profile.status_code == 200
    profile_json = profile.get_json()
    assert profile_json["value"]["username"] == "alice"

    bad_login = client.post("/auth/login", json={"username": "alice", "password": "badpass"})
    assert bad_login.status_code == 401


def test_basic_demo_login_and_profile() -> None:
    """HTTP Basic credentials are required for login and profile."""

    class BasicConfig(BaseConfig):
        API_AUTHENTICATE_METHOD = ["basic"]
        API_USER_MODEL = User
        API_USER_LOOKUP_FIELD = "username"
        API_CREDENTIAL_CHECK_METHOD = "check_password"

    def seed(_: FlaskClient) -> None:
        user = User(username="bob", password="builder")
        db.session.add(user)
        db.session.commit()

    client = _prepare_app(BasicConfig, seed)
    creds = base64.b64encode(b"bob:builder").decode("utf-8")
    resp = client.post("/auth/login", headers={"Authorization": f"Basic {creds}"})
    assert resp.status_code == 200

    profile = client.get("/profile", headers={"Authorization": f"Basic {creds}"})
    assert profile.status_code == 200
    profile_json = profile.get_json()
    assert profile_json["value"]["username"] == "bob"

    bad_creds = base64.b64encode(b"bob:wrongpwd").decode("utf-8")
    bad_login = client.post("/auth/login", headers={"Authorization": f"Basic {bad_creds}"})
    assert bad_login.status_code == 401


def test_api_key_demo_login_and_profile() -> None:
    """API keys authenticate requests to the profile endpoint."""

    def lookup_user_by_token(token: str) -> User | None:
        user = User.query.filter_by(api_key=token).first()
        if user:
            set_current_user(user)
        return user

    class KeyConfig(BaseConfig):
        API_AUTHENTICATE_METHOD = ["api_key"]
        API_USER_MODEL = User
        API_KEY_AUTH_AND_RETURN_METHOD = staticmethod(lookup_user_by_token)
        API_USER_LOOKUP_FIELD = "username"

    def seed(_: FlaskClient) -> None:
        user = User(username="carol", password="pw", api_key="secret")
        db.session.add(user)
        db.session.commit()

    client = _prepare_app(KeyConfig, seed)
    headers = {"Authorization": "Api-Key secret"}
    resp = client.post("/auth/login", headers=headers)
    assert resp.status_code == 200

    profile = client.get("/profile", headers=headers)
    assert profile.status_code == 200
    profile_json = profile.get_json()
    assert profile_json["value"]["username"] == "carol"

    bad_login = client.post("/auth/login", headers={"Authorization": "Api-Key bad"})
    assert bad_login.status_code == 401
