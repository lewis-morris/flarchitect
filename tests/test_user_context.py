"""Tests for clearing user context after requests."""

from flask import Flask

from flarchitect.authentication.user import (
    get_current_user,
    register_user_teardown,
    set_current_user,
)


def test_register_user_teardown_clears_context() -> None:
    """Teardown handler removes the current user after each request."""
    app = Flask(__name__)
    register_user_teardown(app)

    @app.route("/")
    def index() -> str:
        set_current_user("alice")
        return "ok"

    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert get_current_user() is None
    resp = client.get("/")
    assert resp.status_code == 200
    assert get_current_user() is None
