import types

import pytest

from demo.authentication.app_base import BaseConfig, User, create_app, db
from flarchitect.authentication.user import set_current_user


class Config(BaseConfig):
    API_AUTHENTICATE_METHOD = ["custom"]
    API_USER_MODEL = User
    API_AUTH_ME_ROUTE = "/api/auth/me"


@pytest.fixture
def app():
    # Provide a custom auth function that sets current_user
    def _custom_auth():
        # create an in-memory user instance
        usr = User(id=1, username="alice", password="secret", roles=[])
        set_current_user(usr)
        return True

    Config.API_CUSTOM_AUTH = staticmethod(_custom_auth)
    app = create_app(Config)
    with app.app_context():
        db.create_all()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_me_route_uses_configured_path(client):
    r = client.get("/api/auth/me")
    data = r.get_json()
    assert data["status_code"] == 200
    assert data["value"]["username"] == "alice"


def test_me_route_respects_api_expose_me_flag():
    # Build a separate app instance with API_EXPOSE_ME disabled
    from demo.authentication.app_base import BaseConfig, create_app, db, User

    class DisabledConfig(BaseConfig):
        API_AUTHENTICATE_METHOD = ["custom"]
        API_USER_MODEL = User
        API_AUTH_ME_ROUTE = "/api/auth/me"
        API_EXPOSE_ME = False

    def _custom_auth():
        # still sets a user, but route should not be registered
        set_current_user(User(id=1, username="alice", password="secret", roles=[]))
        return True

    DisabledConfig.API_CUSTOM_AUTH = staticmethod(_custom_auth)
    app2 = create_app(DisabledConfig)
    with app2.app_context():
        db.create_all()
    client2 = app2.test_client()
    r = client2.get("/api/auth/me")
    assert r.status_code == 404
