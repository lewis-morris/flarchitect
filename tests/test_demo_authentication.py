"""Tests for the authentication demo application."""

from __future__ import annotations

from base64 import b64encode

from flask.testing import FlaskClient

from demo.authentication.app_base import User, db
from demo.authentication.basic_auth import app


def test_basic_auth_login() -> None:
    """User can log in using HTTP Basic credentials."""
    with app.app_context():
        db.session.add(User(username="alice", password="wonderland", api_key="unused"))
        db.session.commit()

    client: FlaskClient = app.test_client()
    credentials = b64encode(b"alice:wonderland").decode()
    response = client.post("/auth/login", headers={"Authorization": f"Basic {credentials}"})

    assert response.status_code == 200
    assert response.get_json()["value"]["username"] == "alice"
