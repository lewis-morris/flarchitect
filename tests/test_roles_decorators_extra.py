import pytest
from flask import Flask

from flarchitect.authentication.roles import (
    _build_user_context,
    _forbidden_with_context,
    _infer_resource_from_path,
    roles_accepted,
    roles_required,
)
from flarchitect.authentication.user import set_current_user
from flarchitect.exceptions import CustomHTTPException


class U:
    def __init__(self, roles):
        self.roles = roles


def test_roles_required_and_accepted():
    @roles_required("admin", "editor")
    def fn1():
        return "ok"

    @roles_accepted("user", "moderator")
    def fn2():
        return "ok"

    # Unauthenticated
    set_current_user(None)
    with pytest.raises(CustomHTTPException):
        fn1()

    # Missing one role -> forbidden for roles_required
    set_current_user(U(["admin"]))
    with pytest.raises(CustomHTTPException):
        fn1()

    # Any of -> allowed when one matches
    set_current_user(U(["moderator"]))
    assert fn2() == "ok"

    app = Flask(__name__)
    with app.test_request_context("/api/widgets", method="GET"):
        set_current_user(U(["guest"]))
        forbidden = fn2()
    assert forbidden.status_code == 403

    set_current_user(U(["admin", "editor"]))
    assert fn1() == "ok"


def test_role_context_uses_current_user_and_request_path(monkeypatch):
    app = Flask(__name__)
    app.config["API_PREFIX"] = "/api"
    user = U(["admin"])
    user.id = 9
    user.username = "alice"

    monkeypatch.setattr("flarchitect.authentication.jwt.get_pk_and_lookups", lambda: ("id", "username"))

    with app.test_request_context("/api/widgets/1"):
        set_current_user(user)
        user_ctx, lookup_ctx = _build_user_context()

        assert user_ctx == {"id": 9, "username": "alice", "roles": ["admin"]}
        assert lookup_ctx == {"pk": 9, "lookups": {"username": "alice"}}
        assert _infer_resource_from_path() == "widgets"


def test_role_context_can_decode_bearer_user_when_current_user_missing(monkeypatch):
    app = Flask(__name__)
    token_user = U(["reader"])
    token_user.id = 11
    token_user.username = "token-user"

    monkeypatch.setattr("flarchitect.authentication.jwt.get_pk_and_lookups", lambda: ("id", "username"))
    monkeypatch.setattr("flarchitect.authentication.jwt.get_user_from_token", lambda token, secret_key=None: token_user)

    with app.test_request_context("/api/widgets", headers={"Authorization": "Bearer abc"}):
        set_current_user(None)
        user_ctx, lookup_ctx = _build_user_context()

    assert user_ctx == {"id": 11, "username": "token-user", "roles": ["reader"]}
    assert lookup_ctx == {"pk": 11, "lookups": {"username": "token-user"}}


def test_forbidden_response_prefers_resolved_role_map_and_endpoint_fallback():
    app = Flask(__name__)
    app.config["API_ROLE_MAP"] = {"GET": {"roles": ["reader"], "any_of": True}}
    app.config["API_PREFIX"] = "/v1"

    user = U(["guest"])
    user.id = 7
    user.username = "guest-user"

    with app.test_request_context("/outside/path", method="GET"):
        set_current_user(user)
        response = _forbidden_with_context(
            provided_roles=["guest"],
            required_roles=["admin"],
            any_of=False,
            reason="missing_roles",
        )

    assert response.status_code == 403
    errors = response.get_json()["errors"]
    assert errors["required_roles"] == ["reader"]
    assert errors["any_of"] is True
    assert errors["resource"] is None
    assert errors["resolved_from"] == "GET"
    assert errors["user"]["roles"] == ["guest"]
